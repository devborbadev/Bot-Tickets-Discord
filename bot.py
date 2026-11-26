import asyncio
import io
import logging
import os
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
_GUILD_ID_RAW = os.getenv("GUILD_ID")
_STAFF_ROLE_ID_RAW = os.getenv("STAFF_ROLE_ID")
_LOG_CHANNEL_ID_RAW = os.getenv("LOG_CHANNEL_ID")

CATEGORY_NAME = "🎫 Tickets"
MAX_CHANNELS_PER_CATEGORY = 50

log = logging.getLogger("ticket-bot")

_faltando = [
    nome
    for nome, valor in {
        "DISCORD_TOKEN": TOKEN,
        "GUILD_ID": _GUILD_ID_RAW,
        "STAFF_ROLE_ID": _STAFF_ROLE_ID_RAW,
    }.items()
    if not valor
]
if _faltando:
    raise SystemExit(
        "Faltam variáveis de ambiente obrigatórias: "
        + ", ".join(_faltando)
        + ". Configure-as no arquivo .env (local) ou em 'Variables' (Railway)."
    )

try:
    GUILD_ID = int(_GUILD_ID_RAW)
    STAFF_ROLE_ID = int(_STAFF_ROLE_ID_RAW)
    LOG_CHANNEL_ID = int(_LOG_CHANNEL_ID_RAW) if _LOG_CHANNEL_ID_RAW else None
except ValueError:
    raise SystemExit(
        "GUILD_ID, STAFF_ROLE_ID e LOG_CHANNEL_ID devem ser números (IDs do Discord)."
    )

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

_criando_agora: set[int] = set()

TIPOS_TICKET = {
    "ticket_venda": "Venda de Contas",
    "ticket_compra": "Compra de Conta",
    "ticket_scammer": "Reporte de Scammer",
    "ticket_duvidas": "Dúvidas",
}

def sanitize_name(texto: str) -> str:
    texto = texto.lower().strip()
    seguro = "".join(c if c.isalnum() else "-" for c in texto)
    while "--" in seguro:
        seguro = seguro.replace("--", "-")
    seguro = seguro.strip("-")
    return seguro[:20] or "usuario"

async def get_or_create_category(guild: discord.Guild) -> discord.CategoryChannel:
    categoria = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if categoria is not None:
        return categoria

    staff_role = guild.get_role(STAFF_ROLE_ID)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True),
    }
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True)

    categoria = await guild.create_category(CATEGORY_NAME, overwrites=overwrites)
    log.info("Categoria '%s' criada.", CATEGORY_NAME)
    return categoria

def find_open_ticket(categoria: discord.CategoryChannel, user_id: int) -> discord.TextChannel | None:
    marcador = f"uid:{user_id}"
    for canal in categoria.text_channels:
        if canal.topic and marcador in canal.topic:
            return canal
    return None

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _handle(self, interaction: discord.Interaction, custom_id: str):
        tipo = TIPOS_TICKET[custom_id]
        user = interaction.user
        guild = interaction.guild

        if user.id in _criando_agora:
            await interaction.response.send_message(
                "Estou processando seu pedido anterior, aguarde um instante...",
                ephemeral=True,
            )
            return

        _criando_agora.add(user.id)
        try:
            await interaction.response.defer(ephemeral=True)

            categoria = await get_or_create_category(guild)

            existente = find_open_ticket(categoria, user.id)
            if existente:
                await interaction.followup.send(
                    f"Você já tem um ticket aberto: {existente.mention}", ephemeral=True
                )
                return

            if len(categoria.channels) >= MAX_CHANNELS_PER_CATEGORY:
                await interaction.followup.send(
                    "O sistema de tickets está lotado no momento. Chame um administrador.",
                    ephemeral=True,
                )
                log.warning("Categoria de tickets cheia (limite de %s canais).", MAX_CHANNELS_PER_CATEGORY)
                return

            staff_role = guild.get_role(STAFF_ROLE_ID)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, manage_channels=True
                ),
                user: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                ),
            }
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    manage_messages=True,
                    read_message_history=True,
                )

            nome_canal = f"{sanitize_name(tipo)}-{sanitize_name(user.name)}"
            novo_canal = await guild.create_text_channel(
                name=nome_canal,
                category=categoria,
                overwrites=overwrites,
                topic=f"Tipo: {tipo} | Aberto por {user} | uid:{user.id}",
                reason=f"Ticket criado por {user} ({user.id})",
            )

            embed = discord.Embed(
                title=f"🎫 {tipo}",
                description=(
                    f"Olá {user.mention}! Seu ticket foi criado.\n"
                    "Descreva o que você precisa e aguarde a equipe responder.\n\n"
                    "Quando terminar, clique em **Fechar Ticket** abaixo."
                ),
                color=discord.Color.blurple(),
                timestamp=datetime.now(timezone.utc),
            )
            allowed = discord.AllowedMentions(users=True, roles=True, everyone=False)
            conteudo = user.mention
            if staff_role:
                conteudo += f" {staff_role.mention}"

            await novo_canal.send(
                content=conteudo, embed=embed, view=CloseTicketView(), allowed_mentions=allowed
            )

            await interaction.followup.send(f"Ticket criado: {novo_canal.mention}", ephemeral=True)
            log.info("Ticket '%s' criado por %s (%s).", tipo, user, user.id)

        except discord.Forbidden:
            log.error("Permissão insuficiente ao criar ticket para %s.", user.id)
            await interaction.followup.send(
                "Não tenho permissão suficiente para criar o canal. Avise um administrador "
                "(preciso de 'Gerenciar Canais' e 'Gerenciar Cargos').",
                ephemeral=True,
            )
        except Exception:
            log.exception("Erro inesperado ao criar ticket.")
            await interaction.followup.send(
                "Ocorreu um erro inesperado ao criar seu ticket. A equipe foi avisada pelos logs.",
                ephemeral=True,
            )
        finally:
            _criando_agora.discard(user.id)

    @discord.ui.button(label="Venda de contas", style=discord.ButtonStyle.success, custom_id="ticket_venda")
    async def venda(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "ticket_venda")

    @discord.ui.button(label="Compra de conta", style=discord.ButtonStyle.primary, custom_id="ticket_compra")
    async def compra(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "ticket_compra")

    @discord.ui.button(label="Reporte um Scammer", style=discord.ButtonStyle.danger, custom_id="ticket_scammer")
    async def scammer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "ticket_scammer")

    @discord.ui.button(label="Dúvidas", style=discord.ButtonStyle.secondary, custom_id="ticket_duvidas")
    async def duvidas(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "ticket_duvidas")

def is_staff_or_owner(member: discord.Member, channel: discord.TextChannel) -> bool:
    if channel.permissions_for(member).manage_channels:
        return True
    staff_role = member.guild.get_role(STAFF_ROLE_ID)
    if staff_role and staff_role in member.roles:
        return True
    return bool(channel.topic and f"uid:{member.id}" in channel.topic)

class ConfirmCloseView(discord.ui.View):
    def __init__(self, quem_fechou: discord.Member):
        super().__init__(timeout=60)
        self.quem_fechou = quem_fechou

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.quem_fechou.id:
            await interaction.response.send_message("Apenas quem clicou pode confirmar.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirmar fechamento", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal = interaction.channel
        await interaction.response.edit_message(content="Fechando o ticket em 5 segundos...", view=None)

        if LOG_CHANNEL_ID:
            try:
                await send_transcript(canal)
            except Exception:
                log.exception("Falha ao gerar o transcript do canal %s.", canal.id)

        await asyncio.sleep(5)
        await canal.delete(reason=f"Ticket fechado por {interaction.user}")

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Fechamento cancelado.", view=None)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff_or_owner(interaction.user, interaction.channel):
            await interaction.response.send_message(
                "Só quem abriu o ticket ou a equipe pode fechá-lo.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "Tem certeza que deseja fechar este ticket?",
            view=ConfirmCloseView(interaction.user),
            ephemeral=True,
        )

async def send_transcript(channel: discord.TextChannel):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel is None:
        return
    linhas = []
    async for msg in channel.history(limit=None, oldest_first=True):
        linhas.append(f"[{msg.created_at:%d/%m/%Y %H:%M}] {msg.author}: {msg.content}")
    conteudo = "\n".join(linhas) or "(sem mensagens)"
    arquivo = discord.File(fp=io.BytesIO(conteudo.encode("utf-8")), filename=f"transcript-{channel.name}.txt")
    await log_channel.send(content=f"📄 Transcript de **{channel.name}**", file=arquivo)

@bot.tree.command(name="painel-tickets", description="Publica o painel de tickets neste canal.")
@app_commands.checks.has_permissions(manage_guild=True)
async def painel_tickets(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Bem-vindo aos Tickets",
        description=(
            "Bem-vindo aos tickets, nele você poderá tirar dúvidas, fazer denúncias "
            "de scammer, vender suas contas, também comprar contas!"
        ),
        color=discord.Color.blurple(),
    )
    await interaction.channel.send(embed=embed, view=TicketPanelView())
    await interaction.response.send_message("Painel publicado com sucesso!", ephemeral=True)

@painel_tickets.error
async def painel_tickets_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "Você precisa da permissão 'Gerenciar Servidor' para usar este comando.", ephemeral=True
        )
        return
    log.error("Erro no comando /painel-tickets.", exc_info=error)
    msg = "Ocorreu um erro inesperado."
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)

@bot.event
async def setup_hook():
    bot.add_view(TicketPanelView())
    bot.add_view(CloseTicketView())

    guild_obj = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild_obj)
    try:
        await bot.tree.sync(guild=guild_obj)
    except discord.Forbidden:
        log.error(
            "Não consegui sincronizar os comandos (/) neste servidor (403 Missing Access). "
            "Gere um novo link em OAuth2 > URL Generator marcando TAMBÉM 'applications.commands' "
            "(além de 'bot') e reautorize o bot no servidor."
        )
    except Exception:
        log.exception("Erro inesperado ao sincronizar os comandos (/).")

@bot.event
async def on_ready():
    log.info("Bot conectado como %s (ID: %s). Pronto para uso.", bot.user, bot.user.id)

if __name__ == "__main__":
    bot.run(TOKEN)
