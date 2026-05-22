import rclpy
from rclpy.node import Node
from turtlesim.srv import TeleportAbsolute, SetPen

# Importa a função de visão computacional do image_processor.
# Toda a pipeline de CV (gaussiano, sobel, limiarização, mapeamento)
# está encapsulada em get_edge_points() — definida em image_processor.py
from image_processor import get_edge_points


# =============================================================
# NÓ ROS 2
# Usa teleport para ir a cada ponto e marca com um ponto.
# A caneta só fica abaixada por um instante em cada ponto.
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

    # Chama o image_processor para processar a imagem e obter os pontos de borda
    # já mapeados para o espaço do Turtlesim
    points = get_edge_points('dog.jpg', max_points=800, threshold=80)

    node = TurtleDraw(points)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()