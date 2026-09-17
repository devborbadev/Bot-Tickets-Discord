# Bot de Tickets — Discord

Bot em Python (discord.py) que publica um painel com 4 botões e cria um canal
de ticket privado para cada solicitação.

## O que ele faz

- Publica uma mensagem com 4 botões: **Venda de contas** (verde), **Compra de
  conta** (azul), **Reporte um Scammer** (vermelho) e **Dúvidas** (cinza —
  o Discord não tem um estilo de botão branco, esse é o mais próximo).
- Ao clicar, cria um canal privado dentro da categoria "🎫 Tickets", visível só
  para quem abriu e para o cargo de staff.
- Impede que a mesma pessoa abra 2 tickets ao mesmo tempo.
- Tem um botão "Fechar Ticket" com confirmação, que apaga o canal.
- Opcionalmente salva um transcript em .txt num canal de logs antes de apagar.

## Arquivos

| Arquivo | Para quê serve |
|---|---|
| `bot.py` | Código do bot |
| `requirements.txt` | Lista de bibliotecas Python necessárias |
| `.env.example` | Modelo das variáveis de configuração (copie para `.env`) |
| `.gitignore` | Evita que o `.env` (com o Token) vá parar no GitHub |

## Variáveis de ambiente

| Nome | Obrigatória? | O que é |
|---|---|---|
| `DISCORD_TOKEN` | Sim | Token do bot |
| `GUILD_ID` | Sim | ID do seu servidor |
| `STAFF_ROLE_ID` | Sim | ID do cargo que vê/gerencia os tickets |
| `LOG_CHANNEL_ID` | Não | ID do canal onde salvar o transcript ao fechar |

## Comandos

- `/painel-tickets` — publica o painel no canal atual. Só funciona para quem
  tem a permissão "Gerenciar Servidor".

## Revisão de segurança

Importante ser honesto sobre isto: como o bot ainda não está rodando num
servidor real, não existe like "atacar" um sistema que ainda não existe.
O que foi feito em vez disso — e que cobre o mesmo objetivo — foi:

1. Instalar a própria biblioteca discord.py 2.7.1 num ambiente de teste e
   confirmar, no código-fonte real dela, a sintaxe usada aqui (assinatura de
   `defer()`, `add_view()`, `interaction_check()`, permissões, etc.).
2. Importar o `bot.py` com valores fictícios e checar que as views (painel e
   botão de fechar) se instanciam sem erro e ficam marcadas como
   **persistentes** (sobrevivem a um restart do bot).
3. Testar a função que gera o nome dos canais com entradas normais e com
   entradas "hostis" (só símbolos, texto vazio) para garantir que nunca gera
   um nome de canal inválido ou quebra o bot.
4. Conferir, um a um, os seguintes pontos de segurança:

| # | Verificação | Como é tratado |
|---|---|---|
| 1 | Vazamento do Token | Fica só em variável de ambiente / `.env`, que está no `.gitignore` |
| 2 | Intents privilegiadas | Nenhuma é usada — o bot não lê mensagens de ninguém |
| 3 | Quem vê o canal do ticket | `@everyone` bloqueado; só o autor + cargo staff + bot |
| 4 | Quem pode fechar um ticket | Só staff, o próprio autor, ou quem tem "Gerenciar Canais" |
| 5 | Fechamento acidental | Exige um clique de confirmação antes de apagar o canal |
| 6 | Cliques duplos/corrida | Trava em memória evita 2 canais para o mesmo clique |
| 7 | Spam de tickets | 1 ticket aberto por pessoa por vez |
| 8 | Limite do Discord (50 canais/categoria) | Verificado antes de criar, com aviso amigável |
| 9 | Menções indevidas (@everyone no ticket) | `allowed_mentions` restrito ao autor + cargo staff |
| 10 | Privilégio do bot | Pede só as permissões necessárias, nunca "Administrador" |
| 11 | Erros expostos ao usuário | Qualquer erro é capturado; o usuário só vê uma mensagem genérica, o detalhe fica no log do servidor |
| 12 | Quem pode publicar/reconfigurar o painel | Só quem tem "Gerenciar Servidor" |

Nenhum sistema é 100% garantido contra falhas, mas esses são os riscos mais
comuns em bots de ticket e todos foram tratados.
