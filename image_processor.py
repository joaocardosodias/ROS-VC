import cv2
import numpy as np
import matplotlib.pyplot as plt


# kernel gaussiano 2D — usado pra suavizar a imagem antes do sobel
# o sigma controla o quanto borra. 1.4 foi o que funcionou melhor nos testes
def gaussian_kernel(size=5, sigma=1.4):
    ax = np.arange(-(size // 2), size // 2 + 1)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
    return kernel / kernel.sum()  # normaliza pra soma = 1

#funçao que aplica as mascaras/filtros
def convolve(image, kernel):
    pad = kernel.shape[0] // 2
    padded = np.pad(image, pad, mode='reflect')
    output = np.zeros_like(image)
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            output[i, j] = np.sum(
                padded[i:i+kernel.shape[0], j:j+kernel.shape[1]] * kernel
            )
    return output


# operador de sobel — detecta onde tem mudança brusca de intensidade (bordas)
# aplica dois kernels: um na direcao x e outro na y, depois combina com a magnitude
def sobel(image):
    # gradiente horizontal
    Kx = np.array([[-1, 0, 1],
                   [-2, 0, 2],
                   [-1, 0, 1]], dtype=np.float64)

    # gradiente vertical
    Ky = np.array([[-1, -2, -1],
                   [ 0,  0,  0],
                   [ 1,  2,  1]], dtype=np.float64)

    Gx = convolve(image, Kx)
    Gy = convolve(image, Ky)

    # magnitude do gradiente — combina as duas direções
    magnitude = np.sqrt(Gx**2 + Gy**2)
    return magnitude / magnitude.max() * 255  # normaliza pra 0-255


def get_edge_points(image_path, max_points=800, threshold=80):
    """
    Função principal da pipeline de visão computacional.

    Recebe o caminho de uma imagem e devolve os pontos de borda
    já mapeados pro espaço do turtlesim (x e y entre 0.5 e 10.5).

    Parametros:
        image_path  -- caminho pra imagem
        max_points  -- quantos pontos retornar no maximo (padrão: 800)
        threshold   -- limiar pra binarizacao, de 0 a 255 (padrão: 80)
    """
    
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise FileNotFoundError(f"nao encontrei a imagem: {image_path}")

    # converte a imagem de BGR para escala de cinza usando a fórmula de luminância do NumPy e transforma para float64
    img = (0.299 * img_bgr[:, :, 2] + 0.587 * img_bgr[:, :, 1] + 0.114 * img_bgr[:, :, 0]).astype(np.float64)

    # suaviza pra reduzir ruido antes do sobel
    blurred = convolve(img, gaussian_kernel())

    # detecta as bordas
    edges = sobel(blurred)

    # limiarizacao: pixel acima do threshold vira branco (borda), resto vira preto
    binary = (edges > threshold).astype(np.uint8) * 255

    # pega as coordenadas dos pixels de borda
    points = np.argwhere(binary > 0)

    # amostra pra nao mandar pontos demais pro turtlesim
    if len(points) > max_points:
        idx = np.linspace(0, len(points) - 1, max_points, dtype=int)
        points = points[idx]

    # mapeia de coordenadas de pixel pra coordenadas do turtlesim
    # o eixo y é invertido porque na imagem (0,0) é no canto superior esquerdo
    # e no turtlesim o (0,0) é no canto inferior esquerdo
    h, w = img.shape
    mapped = np.zeros((len(points), 2), dtype=np.float64)
    mapped[:, 0] = 0.5 + (points[:, 1] / w) * 10.0   # coluna -> x
    mapped[:, 1] = 10.5 - (points[:, 0] / h) * 10.0  # linha  -> y (invertido)

    return mapped


# esse bloco só executa se rodar o arquivo diretamente
# serve pra visualizar as etapas do processamento
if __name__ == '__main__':
    IMAGE_PATH = 'dog.jpg'

    img_bgr = cv2.imread(IMAGE_PATH)
    img = (0.299 * img_bgr[:, :, 2] + 0.587 * img_bgr[:, :, 1] + 0.114 * img_bgr[:, :, 0]).astype(np.float64)

    blurred = convolve(img, gaussian_kernel())
    edges = sobel(blurred)

    threshold = 80
    binary = (edges > threshold).astype(np.uint8) * 255

    # mostra as 3 etapas lado a lado
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    axes[0].imshow(img, cmap='gray')
    axes[0].set_title('1. Escala de Cinza')
    axes[1].imshow(edges, cmap='gray')
    axes[1].set_title('2. Bordas (Sobel)')
    axes[2].imshow(binary, cmap='gray')
    axes[2].set_title('3. Limiarizacao')
    for ax in axes:
        ax.axis('off')
    plt.tight_layout()
    plt.show()

    points = np.argwhere(binary > 0)
    print(f"Total de pontos de borda: {len(points)}")