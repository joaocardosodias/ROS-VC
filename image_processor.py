# importa as bibliotecas necessárias
import cv2
import numpy as np
import matplotlib.pyplot as plt


# Função para criar um kernel Gaussiano 2D. Esse kernel é usado para suavizar a imagem antes da detecção de bordas.
# O size define a largura/altura do kernel, e sigma controla a quantidade de desfoque.
def gaussian_kernel(size=5, sigma=1.4):
    ax = np.arange(-(size // 2), size // 2 + 1)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
    # normaliza para que a soma dos elementos seja igual a 1
    return kernel / kernel.sum()


# A convolução de imagem é uma operação matemática que aplica um filtro (ou máscara) aos pixels de uma imagem para transformá-la
def convolve(image, kernel):
    pad = kernel.shape[0] // 2
    # mode='reflect' evita o artefato de borda preta que ocorre com padding de zeros
    padded = np.pad(image, pad, mode='reflect')
    output = np.zeros_like(image)
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            output[i, j] = np.sum(
                padded[i:i+kernel.shape[0], j:j+kernel.shape[1]] * kernel
            )
    return output


# Função que detecta bordas usando o operador de Sobel. Ele calcula a aproximação do gradiente de intensidade da imagem,
# destacando áreas de alto contraste onde ocorrem mudanças abruptas de cor.
# O Sobel calcula a derivada da imagem nas direções x e y. Ou seja o operador utiliza duas máscaras de convolução
# (filtros) de tamanho 3x3
def sobel(image):
    # Kernel Sobel para derivada na direção x que aplica matriz Gx
    Kx = np.array([[-1, 0, 1],
                   [-2, 0, 2],
                   [-1, 0, 1]], dtype=np.float64)

    # Kernel Sobel para derivada na direção y que aplica matriz Gy
    Ky = np.array([[-1, -2, -1],
                   [ 0,  0,  0],
                   [ 1,  2,  1]], dtype=np.float64)

    # Aplica convolução com os kernels de Sobel que detectam bordas nas direções x e y, respectivamente
    Gx = convolve(image, Kx)
    Gy = convolve(image, Ky)

    # Magnitude do gradiente: intensidade da borda
    magnitude = np.sqrt(Gx**2 + Gy**2)
    # Normaliza para o intervalo 0-255 para exibição
    return magnitude / magnitude.max() * 255


def get_edge_points(image_path, max_points=800, threshold=80):
    """
    Pipeline completa de visão computacional.

    Recebe o caminho de uma imagem e retorna um array (N, 2) com as
    coordenadas dos pontos de borda já mapeados para o espaço do Turtlesim
    (x e y entre 0.5 e 10.5).

    Etapas:
        1. Carregamento com OpenCV (único uso permitido)
        2. Conversão para escala de cinza
        3. Suavização com filtro Gaussiano (convolução manual)
        4. Detecção de bordas com operador Sobel (convolução manual)
        5. Limiarização binária
        6. Amostragem e mapeamento para coordenadas do Turtlesim

    Parâmetros:
        image_path (str): Caminho para a imagem de entrada.
        max_points  (int): Número máximo de pontos a retornar (padrão: 800).
        threshold   (int): Limiar de intensidade para considerar um pixel como
                           borda, de 0 a 255 (padrão: 80).

    Retorna:
        numpy.ndarray: Array de forma (N, 2) com colunas [x_turtlesim, y_turtlesim].
    """
    # 1. Carrega a imagem usando OpenCV (conforme permitido pelo enunciado)
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

    # 2. Converte para escala de cinza e float64 para operações numéricas
    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)

    # 3. Aplica suavização Gaussiana para reduzir ruído antes do Sobel
    blurred = convolve(img, gaussian_kernel())

    # 4. Detecta bordas com o operador de Sobel
    edges = sobel(blurred)

    # 5. Limiarização: pixels acima do threshold viram 255, resto vira 0
    binary = (edges > threshold).astype(np.uint8) * 255

    # 6. Extrai as coordenadas (linha, coluna) de cada pixel de borda
    points = np.argwhere(binary > 0)

    # Amostra para não exceder max_points (mantém distribuição uniforme)
    if len(points) > max_points:
        idx = np.linspace(0, len(points) - 1, max_points, dtype=int)
        points = points[idx]

    # Mapeia coordenadas de pixel para o espaço do Turtlesim (0.5 a 10.5)
    h, w = img.shape
    mapped = np.zeros((len(points), 2), dtype=np.float64)
    mapped[:, 0] = 0.5 + (points[:, 1] / w) * 10.0   # coluna → x
    mapped[:, 1] = 10.5 - (points[:, 0] / h) * 10.0  # linha  → y (invertido)

    return mapped


# =============================================================================
# Bloco de visualização — executa somente quando rodado diretamente
# (não é importado pelo turtle_draw.py)
# =============================================================================
if __name__ == '__main__':
    IMAGE_PATH = 'dog.jpg'

    # abre a imagem em cores usando OpenCV (BGR)
    img_bgr = cv2.imread(IMAGE_PATH)

    # converte a imagem de BGR para escala de cinza e transforma para float64
    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)

    # Aplica suavização Gaussiana à imagem em escala de cinza
    blurred = convolve(img, gaussian_kernel())

    # Calcula a imagem de bordas a partir da imagem suavizada
    edges = sobel(blurred)

    # Limiarização
    threshold = 80
    binary = (edges > threshold).astype(np.uint8) * 255

    # Exibe as imagens para visualização
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    axes[0].imshow(img, cmap='gray')
    axes[0].set_title('1. Escala de Cinza')
    axes[1].imshow(edges, cmap='gray')
    axes[1].set_title('2. Bordas (Sobel)')
    axes[2].imshow(binary, cmap='gray')
    axes[2].set_title('3. Limiarização')
    for ax in axes:
        ax.axis('off')
    plt.tight_layout()
    plt.show()

    # Resultado: encontra os pontos de borda na imagem binária
    points = np.argwhere(binary > 0)
    print(f"Total de pontos de borda: {len(points)}")