import rclpy
from rclpy.node import Node
from turtlesim.srv import TeleportAbsolute, SetPen
import numpy as np
import cv2
import os
from ament_index_python.packages import get_package_share_directory


def get_image_path():
    pkg_share = get_package_share_directory('turtle_draw_pkg')
    return os.path.join(pkg_share, 'resources', 'dog.jpg')


# =============================================================
# PROCESSAMENTO DA IMAGEM
# Extrai os pontos de borda e mapeia para o espaço do turtlesim
# =============================================================
def get_edge_points(image_path, max_points=3000):
    # Carregar imagem (único uso permitido do OpenCV)
    img_bgr = cv2.imread(image_path)
    # Converter para cinza e float64 usando NumPy (luminância)
    # B = canal 0, G = canal 1, R = canal 2
    img = (0.299 * img_bgr[:, :, 2] + 0.587 * img_bgr[:, :, 1] + 0.114 * img_bgr[:, :, 0]).astype(np.float64)

    # Filtro Gaussiano para suavizar e reduzir ruído
    def gaussian_kernel(size=5, sigma=1.4):
        ax = np.arange(-(size // 2), size // 2 + 1)
        xx, yy = np.meshgrid(ax, ax)
        kernel = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
        return kernel / kernel.sum()

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

    # Sobel: detecta bordas em X e Y e combina
    def sobel(image):
        Kx = np.array([[-1, 0, 1],
                       [-2, 0, 2],
                       [-1, 0, 1]], dtype=np.float64)
        Ky = np.array([[-1, -2, -1],
                       [ 0,  0,  0],
                       [ 1,  2,  1]], dtype=np.float64)
        Gx = convolve(image, Kx)
        Gy = convolve(image, Ky)
        magnitude = np.sqrt(Gx**2 + Gy**2)
        return magnitude / magnitude.max() * 255

    blurred = convolve(img, gaussian_kernel())
    edges = sobel(blurred)

    # Limiarização: só mantém bordas fortes
    binary = (edges > 80).astype(np.uint8) * 255

    # Extrair coordenadas dos pixels de borda
    points = np.argwhere(binary > 0)

    # Amostrar para não ter pontos demais
    if len(points) > max_points:
        idx = np.linspace(0, len(points) - 1, max_points, dtype=int)
        points = points[idx]

    # Mapear pixels para coordenadas do turtlesim mantendo aspect ratio
    h, w = img.shape
    aspect = w / h
    sim_size = 10.0  # tamanho do espaço útil do turtlesim (0.5 a 10.5)

    if aspect >= 1:
        # Imagem mais larga que alta: width ocupa tudo, height é escalada
        scale_x = sim_size / w
        scale_y = scale_x
        offset_x = 0.5
        offset_y = 0.5 + (sim_size - h * scale_y) / 2
    else:
        # Imagem mais alta que larga: height ocupa tudo, width é escalado
        scale_y = sim_size / h
        scale_x = scale_y
        offset_y = 0.5
        offset_x = 0.5 + (sim_size - w * scale_x) / 2

    mapped = np.zeros((len(points), 2), dtype=np.float64)
    mapped[:, 0] = offset_x + points[:, 1] * scale_x
    mapped[:, 1] = 11.0 - (offset_y + points[:, 0] * scale_y)

    return mapped


# =============================================================
# NÓ ROS 2
# Usa teleport para ir a cada ponto e marca com um ponto
# A caneta só fica abaixada por um instante em cada ponto
# =============================================================
class TurtleDraw(Node):
    def __init__(self, points):
        super().__init__('turtle_draw')
        self.points = points
        self.index = 0
        self.step = 0  # controla sub-etapas de cada ponto

        # Clientes dos serviços do turtlesim
        self.teleport = self.create_client(TeleportAbsolute, '/turtle1/teleport_absolute')
        self.pen = self.create_client(SetPen, '/turtle1/set_pen')

        # Timer executa draw_step a cada 0.05 segundos
        self.timer = self.create_timer(0.05, self.draw_step)
        self.get_logger().info(f'Desenhando {len(points)} pontos...')

    def set_pen(self, down):
        # Controla se a caneta está levantada (off=1) ou abaixada (off=0)
        req = SetPen.Request()
        req.r, req.g, req.b = 255, 255, 255
        req.width = 3
        req.off = 0 if down else 1
        self.pen.call_async(req)

    def teleport_to(self, x, y):
        req = TeleportAbsolute.Request()
        req.x = float(x)
        req.y = float(y)
        req.theta = 0.0
        self.teleport.call_async(req)

    def draw_step(self):
        if self.index >= len(self.points):
            self.get_logger().info('Desenho concluído!')
            self.timer.cancel()
            return

        x, y = self.points[self.index]

        if self.step == 0:
            self.set_pen(down=False)
            self.teleport_to(x, y)
            self.step = 1

        elif self.step == 1:
            self.set_pen(down=True)
            self.teleport_to(x, y)  # teleporta de novo com caneta abaixada
            self.step = 2

        elif self.step == 2:
            self.set_pen(down=False)
            self.step = 0
            self.index += 1


def main(args=None):
    rclpy.init(args=args)
    image_path = get_image_path()
    points = get_edge_points(image_path, max_points=3000)
    node = TurtleDraw(points)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()