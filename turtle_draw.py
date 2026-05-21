import rclpy
from rclpy.node import Node
from turtlesim.srv import TeleportAbsolute, SetPen
import numpy as np
import cv2


# =============================================================
# PROCESSAMENTO DA IMAGEM
# Extrai os pontos de borda e mapeia para o espaço do turtlesim
# =============================================================
def get_edge_points(image_path, max_points=800):
    # Carregar imagem (único uso permitido do OpenCV)
    img_bgr = cv2.imread(image_path)
    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)

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

    # Mapear pixels para coordenadas do turtlesim (0.5 a 10.5)
    h, w = img.shape
    mapped = np.zeros((len(points), 2), dtype=np.float64)
    mapped[:, 0] = 0.5 + (points[:, 1] / w) * 10.0        # x
    mapped[:, 1] = 10.5 - (points[:, 0] / h) * 10.0       # y invertido

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
    points = get_edge_points('dog.jpg', max_points=800)
    node = TurtleDraw(points)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()