Bot de Tickets — Discord

Bot em Python (discord.py) que publica um painel com 4 botões e cria um canal
de ticket privado para cada solicitação.

O que ele faz?
Publica uma mensagem com 4 botões: Venda de contas (verde), Compra de
  conta (azul), Reporte um Scammer (vermelho) e Dúvidas (cinza).
  
Ao clicar, cria um canal privado dentro da categoria "🎫 Tickets", visível só
para quem abriu e para o cargo de staff.
Impede que a mesma pessoa abra 2 tickets ao mesmo tempo.
Tem um botão "Fechar Ticket" com confirmação, que apaga o canal.
Opcionalmente salva um transcript em .txt num canal de logs antes de apagar.

Comandos
- `/painel-tickets` — publica o painel no canal atual. Só funciona para quem
  tem a permissão "Gerenciar Servidor".
