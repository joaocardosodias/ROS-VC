# Documentação Técnica — Turtle Draw

---

## Pré-processamento

A primeira coisa que fiz foi carregar a imagem e converter pra escala de cinza. Usei o OpenCV apenas para carregar a imagem e o NumPy para realizar a conversão de escala de cinza usando a fórmula de luminância, e daí em diante tudo foi feito com NumPy.

O motivo de converter pra cinza é simples: os filtros que apliquei depois trabalham em matrizes 2D. Se fosse usar os 3 canais de cor ia ter que fazer tudo três vezes sem ganhar nada relevante pra detecção de borda.

Depois da conversão, apliquei um filtro Gaussiano 5x5 pra suavizar a imagem antes de rodar o Sobel. Isso foi necessário porque a foto do cachorro tem bastante textura — pelo, sombra, granulação da parede — e sem suavizar o Sobel ia detectar isso tudo como borda. O resultado ficava uma bagunça de pontos espalhados por toda a imagem.

O kernel Gaussiano foi calculado com a formula `exp(-(x² + y²)/(2σ²))` e normalizado pra somar 1. O sigma que usei foi 1.4, que já é um valor classico pra esse tipo de coisa.

Um detalhe que causou problema no começo: eu estava usando padding com zeros na convolucao. Isso fazia o Sobel detectar uma "borda fantasma" em toda a extremidade da imagem, porque ele via a transição dos pixels da borda pra zero como uma mudança brusca de intensidade. Resolvi trocando pra `mode='reflect'`, que espelha os pixels nas bordas ao invés de colocar zero.

---

## Detecção de Bordas

Escolhi o operador de Sobel porque ele é simples, direto e funciona bem pra esse tipo de imagem com contornos definidos. A ideia é aplicar dois kernels de convolução — um pra detectar mudanças na direção horizontal (Kx) e outro na vertical (Ky) — e combinar os dois resultados calculando a magnitude do gradiente: `√(Gx² + Gy²)`.

No final normalizei o resultado pra ficar entre 0 e 255, o que facilita a etapa de limiarização depois.

O principal desafio aqui foi calibrar o threshold. Com um valor muito baixo (tipo 30 ou 40) o resultado ficava com muito ruido, pegando textura de fundo que não é borda de verdade. Com valor muito alto (acima de 120 ou 150) ia perdendo partes do contorno do cachorro. Fui testando e o valor 80 foi o que deu o melhor equilibrio pra essa imagem especifica.

---

## Planejamento de Caminho

Depois da limiarizacao, o resultado é uma imagem binária onde os pixels brancos são as bordas detectadas. Usei `np.argwhere` pra extrair as coordenadas de todos esses pixels — deu mais de 15 mil pontos.

Mandar 15 mil pontos pro Turtlesim obviamente não seria viável, então amostrei com `np.linspace` pra pegar 800 pontos distribuidos uniformemente ao longo do array. Preferi amostragem uniforme em vez de aleatória pra garantir que todos os contornos tivessem representação.

O mapeamento das coordenadas foi um pouco chatinho porque o sistema de referência do Turtlesim é diferente do da imagem. Na imagem, o (0,0) fica no canto superior esquerdo e o eixo Y cresce pra baixo. No Turtlesim o (0,0) fica no canto inferior esquerdo e o Y cresce pra cima. Então inverti o Y na conversão:

```
x_turtle = 0.5 + (coluna / largura) * 10.0
y_turtle = 10.5 - (linha / altura) * 10.0
```

O offset de 0.5 foi pra dar uma margem nas bordas da janela e evitar que a tartaruga fosse até o limite exato.

---

## Controle ROS 2

Decidi usar `TeleportAbsolute` em vez de publicar velocidades no `cmd_vel`. A razão é que o objetivo aqui é reproduzir o contorno da imagem, não simular o movimento fisico de um robô navegando. Com teleporte, a tartaruga vai diretamente pra cada ponto sem erro de trajetoria, sem precisar de controlador PID ou nada do tipo.

Pra cada ponto, o nó executa um ciclo de 3 passos via timer:
1. Levanta a caneta e teleporta pro ponto
2. Abaixa a caneta e teleporta pro mesmo ponto de novo (pra marcar o pixel)
3. Levanta a caneta e passa pro próximo índice

Uma dificuldade que tive foi organizar o código. No começo coloquei tudo no `turtle_draw.py` — o processamento da imagem e o nó ROS junto. Ficou um arquivo enorme e dificil de mexer. Acabei separando: o `image_processor.py` cuida só da parte de visão, e o `turtle_draw.py` importa a função `get_edge_points()` e foca só no controle da tartaruga. Ficou muito mais limpo assim.
