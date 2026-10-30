Bot de Tickets — Discord

Bot em Python (discord.py) que publica um painel com 4 botões e cria um canal
de ticket privado para cada solicitação.

O que ele faz?
Publica uma mensagem com 4 botões: Venda de contas (verde), Compra de
  conta (azul), Reporte um Scammer (vermelho) e Dúvidas (cinza —
  o Discord não tem um estilo de botão branco, esse é o mais próximo).
Ao clicar, cria um canal privado dentro da categoria "🎫 Tickets", visível só
para quem abriu e para o cargo de staff.
Impede que a mesma pessoa abra 2 tickets ao mesmo tempo.
Tem um botão "Fechar Ticket" com confirmação, que apaga o canal.
Opcionalmente salva um transcript em .txt num canal de logs antes de apagar.

Arquivos
 Arquivo | Para quê serve 
 `bot.py`  Código do bot 
 `requirements.txt` | Lista de bibliotecas Python necessárias |
 `.env.example` | Modelo das variáveis de configuração (copie para `.env`) |
 `.gitignore` | Evita que o `.env` (com o Token) vá parar no GitHub |
 
Variáveis de ambiente
 Nome,  Obrigatória?,  O que é 
|---|---|---|
| `DISCORD_TOKEN` , Sim , Token do bot 
| `GUILD_ID` , Sim , ID do seu servidor 
| `STAFF_ROLE_ID`  Sim,  ID do cargo que vêgerencia os tickets 
| `LOG_CHANNEL_ID`  Não,  ID do canal onde salvar o transcript ao fechar

Comandos
- `/painel-tickets` — publica o painel no canal atual. Só funciona para quem
  tem a permissão "Gerenciar Servidor".
