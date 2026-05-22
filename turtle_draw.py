import rclpy
from rclpy.node import Node
from turtlesim.srv import TeleportAbsolute, SetPen

# importa a funcao de visão computacional do outro arquivo
# toda a pipeline (gaussiano, sobel, limiarizacao, mapeamento) fica la
from image_processor import get_edge_points


class TurtleDraw(Node):
    def __init__(self, points):
        super().__init__('turtle_draw')
        self.points = points
        self.index = 0
        self.step = 0  # controla em qual sub-etapa do ponto atual estamos

        # clientes dos servicos do turtlesim
        self.teleport = self.create_client(TeleportAbsolute, '/turtle1/teleport_absolute')
        self.pen = self.create_client(SetPen, '/turtle1/set_pen')

        # chama draw_step a cada 0.05s
        self.timer = self.create_timer(0.05, self.draw_step)
        self.get_logger().info(f'iniciando desenho de {len(points)} pontos...')

    def set_pen(self, down):
        # off=0 significa caneta ligada (desenhando), off=1 significa desligada
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
        # terminou todos os pontos
        if self.index >= len(self.points):
            self.get_logger().info('desenho concluido!')
            self.timer.cancel()
            return

        x, y = self.points[self.index]

        if self.step == 0:
            # levanta a caneta e vai ate o ponto sem riscar
            self.set_pen(down=False)
            self.teleport_to(x, y)
            self.step = 1

        elif self.step == 1:
            # abaixa a caneta e teleporta pro mesmo lugar — isso marca o ponto
            self.set_pen(down=True)
            self.teleport_to(x, y)
            self.step = 2

        elif self.step == 2:
            # levanta a caneta de novo e avanca pro proximo ponto
            self.set_pen(down=False)
            self.step = 0
            self.index += 1


def main(args=None):
    rclpy.init(args=args)

    # processa a imagem e pega os pontos de borda ja mapeados pro turtlesim
    points = get_edge_points('dog.jpg', max_points=800, threshold=80)

    node = TurtleDraw(points)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()