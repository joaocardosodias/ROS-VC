# Turtle Draw

Projeto da ponderada de Robótica e Visão Computacional. A ideia é pegar uma imagem, extrair os contornos dela usando visao computacional feita na mão (sem bibliotecas prontas), e fazer a tartaruga do Turtlesim desenhar esses contornos.

---

## Demonstração (Vídeo)

Assista ao Screencast demonstrativo do projeto funcionando:
🔗 **[Vídeo da Demonstração no YouTube](https://youtu.be/2YuZff8OVJI)**

---

## Arquivos

```
ROS-VC/
├── dog.jpg               # imagem que eu usei de entrada
├── image_processor.py    # toda a parte de visão computacional
├── turtle_draw.py        # nó ROS 2 que controla a tartaruga
└── README.md
```

---

## Como funciona

O `image_processor.py` cuida de toda a parte de processamento da imagem. Ele tem uma função principal chamada `get_edge_points()` que recebe o caminho da imagem e devolve os pontos de borda já convertidos para as coordenadas do Turtlesim.

O `turtle_draw.py` importa essa função e usa os pontos para desenhar. Ele não tem nenhum codigo de visão computacional dentro, só o nó ROS 2 mesmo.

---

## Rodando

### Só pra ver o processamento da imagem (sem ROS)

```bash
python3 image_processor.py
```

Abre uma janela mostrando as 3 etapas: a imagem em cinza, as bordas detectadas pelo Sobel, e a imagem binarizada.

---

### Pra desenhar no Turtlesim (precisa do ROS 2 instalado)

**Terminal 1:**
```bash
source /opt/ros/humble/setup.bash
ros2 run turtlesim turtlesim_node
```

**Terminal 2:**
```bash
source /opt/ros/humble/setup.bash
python3 turtle_draw.py
```

O script já processa a imagem automaticamente e começa a desenhar. Não precisa rodar o `image_processor.py` antes separado.

> Certifique-se de que o `dog.jpg` está na mesma pasta dos scripts. Se quiser usar outra imagem é so mudar o nome na linha `get_edge_points('dog.jpg', ...)` dentro do `turtle_draw.py`.

---

## Parâmetros

La dentro do `turtle_draw.py`, na chamada da função:

```python
points = get_edge_points('dog.jpg', max_points=800, threshold=80)
```

- `max_points` — quantos pontos a tartaruga vai desenhar. Mais pontos = mais detalhe, mas demora mais
- `threshold` — sensibilidade pra detectar bordas. Valor menor pega mais bordas (e mais ruído também)
