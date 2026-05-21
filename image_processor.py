# importa as bibliotecas necessárias
import cv2
import numpy as np
import matplotlib.pyplot as plt

# abre a imagem em cores usando OpenCV (BGR)
img_bgr = cv2.imread('dog.jpg')

# converte a imagem de BGR para escala de cinza e transforma para float64
# isso facilita o processamento numérico e evita estouros em operações posteriores
img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)

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
    padded = np.pad(image, pad, mode='reflect')
    output = np.zeros_like(image)
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            output[i, j] = np.sum(
                padded[i:i+kernel.shape[0], j:j+kernel.shape[1]] * kernel
            )
    return output

# Aplica suavização Gaussiana à imagem em escala de cinza. Isso reduz ruídos e melhora a qualidade da detecção de bordas.
blurred = convolve(img, gaussian_kernel())


# Função que detecta bordas usando o operador de Sobel. Ele calcula a aproximação do gradiente de intensidade da imagem, destacando áreas de alto contraste onde ocorrem mudanças abruptas de cor.
# O Sobel calcula a derivada da imagem nas direções x e y. Ou seja o operador utiliza duas máscaras de convolução (filtros) de tamanho 3 x 3
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

# Calcula a imagem de bordas a partir da imagem suavizada
edges = sobel(blurred)

# parte de limiarização: converte a imagem de bordas em uma imagem binária, onde os pixels com intensidade acima do limiar são considerados bordas (255) e os demais são considerados fundo (0).
threshold = 80
binary = (edges > threshold).astype(np.uint8) * 255

# Exibe as imgagens para vizualiação.
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