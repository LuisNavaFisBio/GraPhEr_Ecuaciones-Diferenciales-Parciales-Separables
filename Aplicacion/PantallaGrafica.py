from VentanaCarga import Ui_VentanaCarga
from Animaciones import *
from Errores import *

from fractions import Fraction
from matplotlib import cm
from matplotlib.animation import FuncAnimation, FFMpegFileWriter, FFMpegWriter, PillowWriter
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from plasTeX.TeX import TeX
from plasTeX.Renderers.HTML5 import Renderer
from PyQt5.QtCore import QCoreApplication, QMetaObject, QSize, Qt, QUrl, pyqtSignal, QObject, QThreadPool
from PyQt5.QtGui import QFont, QPixmap, QIcon, QMovie
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from sympy import integrate, latex, parsing, pi, preview, symbols, core, I, cos
from sympy.abc import lamda, x, t, n, j
import atexit, os, shutil, matplotlib.widgets, mpl_toolkits.axes_grid1
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import scipy as sc
import sympy as sp
import sys
matplotlib.use('Qt5Agg')

# Determina el directorio actual
directorio_base = os.path.dirname(__file__)

# Este código permite la interpretación rápida de las entradas del usuario, escritas en formato LaTeX, en la pantalla de graficación.
# Dicho código fue tomado y modificado de 
# mugiseyebrows. (31 de marzo 2021). Respuesta a la pregunta "MathJax flickering and statusbar showing in PyQt5". stackoverflow. https://stackoverflow.com/a/66870093
# El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 4.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/4.0/
# La modificación realizada consiste en el cambio del tamaño de letra y los márgenes en #output.
html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="x-ua-compatible" content="ie=edge">
<meta name="viewport" content="width=device-width">
<title>MathJax v3 with interactive TeX input and HTML output</title>
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<script>
    function convert(input) {
    output = document.getElementById('output');
    output.innerHTML = '';
    MathJax.texReset();
    var options = MathJax.getMetricsFor(output);
    options.display = true;
    MathJax.tex2chtmlPromise(input, options).then(function (node) {
        output.appendChild(node);
        MathJax.startup.document.clear();
        MathJax.startup.document.updateDocument();
    }).catch(function (err) {
        output.appendChild(document.createTextNode(err.message));
    });
    }
</script>
<style>
body, html {
    padding: 0;
    margin: 0;
}
#output {
    font-size: 155%;
    min-height: 2em;
    padding: 0;
    margin: 0;
}
.left {
    float: 10em;
}
.right {
    float: 10em;
}
.top {
    float: 60em;
}
</style>
</head>
<body>
<div id="output" class="left"></div>
</body>
</html>
"""

####
class Lienzo(FigureCanvasQTAgg):
    """Clase que contiene el diseño y configuración inicial del lienzo para las gráficas."""
    # El código de esta clase fue modificado de Fitzpatrick, M. (05 de febrero de 2024). Plotting with Matplotlib. Create PyQt5 plots with the popular Python plotting library. PythonGUIs. https://www.pythonguis.com/tutorials/plotting-matplotlib/
    
    def __init__(self, contenedor = None, ancho = 1260, alto = 780, dpi = 100):
        """
        Diseño y configuración del lienzo.
        
        Parámetros
        ----------   
        contenedor** : Parent del widget. No se modifica.

        ancho** : entero
            Ancho en pixeles del lienzo.

        alto** : entero
            Alto en pixeles del lienzo.

        dpi** : entero
            Dots per inch del lienzo.

        visible** : bool
            Determina si el lienzo es visible o no.
        """

        # Diseño del lienzo.
        self.figura = plt.figure(figsize=(ancho/dpi, alto/dpi), dpi=dpi, visible=False)
        super(Lienzo, self).__init__(self.figura)

class GuardadoAnimacion(FuncAnimation):
    """
    Clase que contiene las instrucciones para el proceso de guardado de la animación.
    """

    def __init__(self, canva, func, fargs, interval, maximo = 10, curvas_nivel = False, funcion_curvas = None, numero_introduccion = None, proyeccion = False):
        """
        Inicializa el proceso de guardado.
        
        Parámetros
        ----------
        **Nota: los parámetros func, fargs e interval son los mismos que se especifican en la documentación de la clase FuncAnimation de Matplotlib.**

        canva: Matplotlib.figure
            Figura de Matplotlib que contiene la gráfica.

        maximo: entero
            Número de cuadros totales de la animación.

        curvas_nivel: bool
            Determina si se está guardando la visualización con curvas de nivel.

        funcion_curvas: función de Python
            Función que grafica las curvas de nivel.

        numero_introduccion: entero
            Número de cuadros necesarios para la introducción de la grafica en la animación.

        proyeccion: bool
            Determina si se guarda la proyección o la gráfica sin proyección.
        """

        # Configuración de las variables necesarias.
        self.canva = canva
        self.funcionActualizadora = func
        self.argumentos = fargs
        self.curvas_nivel = curvas_nivel
        self.funcion_curvas = funcion_curvas
        self.proyeccion = proyeccion
        self.umbral = numero_introduccion
        self.numerocuadromaximo = maximo
        self.deslizador = Conteo()
        self.deslizador.val = -2

        # Inicialización del proceso de guardado.
        self.proceso = True
        FuncAnimation.__init__(self, self.canva.figura, self.actualizar, frames = range(-1, self.numerocuadromaximo), interval = interval, repeat=False)
    
    def finalizar(self):
        """
        Función para detener y finalizar el proceso de guardado.
        """

        self.proceso = False
        self.event_source.stop()

    def actualizarGrafica(self, cuadro):
        """
        Actualiza la gráfica con la información del cuadro necesario.
        
        Parámetros
        ----------
        cuadro: entero
            Cuadro actual de la animación.
        """

        self.deslizador.val = cuadro+1-self.umbral-2
        # Actualización de la gráfica.
        self.funcionActualizadora(cuadro, *self.argumentos[0:-2])
        if self.curvas_nivel:
            self.funcion_curvas(guardar = True)
        self.canva.figura.canvas.draw_idle()

    def actualizar(self, indice):
        try:
            print(indice)
            if indice < -1 + self.umbral+2:
                # Creación de los cuadros de introducción de la gráfica en la animación.
                self.funcionActualizadora(indice, *self.argumentos[0:-2])
                if self.curvas_nivel:
                    # Modificación de la opacidad.
                    if self.proyeccion:
                        if len(self.canva.figura.axes) > 8:
                            self.canva.axes.proyeccion.set_alpha(0.4)
                            self.canva.axes2.proyeccion.set_alpha(0.4)
                        else:
                            self.canva.axes.proyeccion.set_alpha(0.4)
                    else:
                        self.canva.axes.superficie.set_alpha(0.4)
            elif indice == -1+self.umbral+2:
                # Adición de la barra de color en la iniciaización.
                self.actualizarGrafica(indice)
                # Agregado de la barra de color para referencia.
                colorbarax = self.canva.figura.add_axes([0.85, 0.15, 0.04, 0.8])
                
                # La creación de la barra de color se basa en mfitzp. (26 de febrero de 2015). Respuesta a la pregunta "Map values to colors in matplotlib". stackoverflow. https://stackoverflow.com/a/28752903
                # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 3.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/3.0/
                plt.colorbar(cm.ScalarMappable(norm=plt.Normalize(-self.argumentos[-3], self.argumentos[-3]), cmap=self.argumentos[-2]), colorbarax)
                
            elif (-1+self.umbral+2 <  indice)  and (indice <= self.numerocuadromaximo-10):
                # Actualización de la animación después de la inicialización.
                self.actualizarGrafica(indice)
            else:
                # Fijación de la gráfica en su último cuadro.
                self.funcionActualizadora(indice, *self.argumentos[0:-2])

            # Visualización de la cuadrícula.    
            if len(self.canva.figura.axes) > 9:
                self.canva.axes.grid(True, lw = 0.2)
                self.canva.axes2.grid(True, lw = 0.2)
            else:
                self.canva.axes.grid(True, lw = 0.2)
            print(True)
        except: 
            exctype, value, line = sys.exc_info()[:3]
            print(exctype, value, line.tb_lineno)
            raise Exception

class Ui_Graficacion(QMainWindow):
    """Clase que contiene el diseño e interactividad de la ventana de visualización de la gráfica."""

    def __init__(self, ventana):
        """
        Inicializa la pantalla de graficación.
        
        Parámetros
        ----------
        ventana** : QMainWindow
            Ventana de la pantalla de graficación.
        """

        super(self.__class__, self).__init__()

        # Señales necesarias para la comunicación con la ventana principal.
        self.signals = Indicadores()

        # Creación de la ventana de graficación.
        self.setupUi(ventana)

    def envioActualizacion(self, mensaje):
        """
        Envía el mensaje a la ventana de carga para informar el punto del trabajo que se está realizando.
        
        Parámetros
        ----------
        mensaje : string
            Mensaje a colocar en la ventana de carga.
        """

        self.signals.avanzar_signal.emit(mensaje)
        QCoreApplication.processEvents()
        QtCore.QThread.msleep(500)

    def setupUi(self, ventana):
        """Diseño y configuración de la ventana principal.
        
        Parámetros
        ----------
        ventana** : QMainWindow
            Ventana de la pantalla principal.
        """
        
        # Algunos aspectos a utilizar de manera repetida.
        # Asigna la imagen a un ícono. Esto se basa en Andy M. (15 de diciembre de 2009). Respuesta a la pregunta "Python QPushButton setIcon: put icon on button". stackoverflow. https://stackoverflow.com/a/1905587
        # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 2.5 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/2.5/
        icono = QIcon()
        icono.addPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "Icono.png")), QIcon.Normal, QIcon.Off)
        
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ventana.sizePolicy().hasHeightForWidth())
        fuente = QFont()
        fuente.setPointSize(10)
        fuente.setBold(True)
        fuente.setWeight(75)

        # Configuración de la ventana.
        ventana.setWindowTitle(u"GraPhEr - Gr\u00e1fica")
        ventana.setWindowIcon(icono)
        ventana.resize(1840, 930)
        ventana.setMinimumSize(QSize(1840, 930))
        ventana.setMaximumSize(QSize(1840, 930))
        ventana.setSizePolicy(sizePolicy)
        ventana.setStyleSheet("color: rgb(246, 247, 247); background-color: rgb(11, 61, 98);")
        self.centralwidget = QWidget(ventana)
        self.centralwidget.setMinimumSize(QSize(1840, 930))
        ventana.setCentralWidget(self.centralwidget)

        frame1 = QFrame(self.centralwidget)
        frame1.setSizePolicy(sizePolicy)
        frame1.setMinimumSize(QSize(1840, 910))
        frame1.setStyleSheet(u"background-color: rgb(11, 61, 98); color: rgb(246, 247, 247)")
        frame1.setFrameShape(QFrame.StyledPanel)
        frame1.setFrameShadow(QFrame.Raised)

        horizontalLayout_1 = QHBoxLayout(frame1)
        horizontalLayout_1.setContentsMargins(10,10,10,10)
        horizontalLayout_1.setStretch(0, 1220)
        horizontalLayout_1.setStretch(1, 5)
        horizontalLayout_1.setStretch(2, 560)
        horizontalLayout_1.setSpacing(10)

        frame2 = QFrame()
        frame2.setSizePolicy(sizePolicy)
        frame2.setMinimumSize(QSize(1220, 905))
        frame2.setMaximumSize(QSize(1220, 905))
        frame2.setStyleSheet(u"color: rgb(246, 247, 247); background-color: rgb(11, 61, 98)")

        # Diseño del cuadro lateral izquierdo (lienzo).
        verticalLayout_1 = QVBoxLayout(frame2)
        verticalLayout_1.setSpacing(10)
        verticalLayout_1.setContentsMargins(0, 0, 0, 0)
        verticalLayout_1.setStretch(0, 30)
        verticalLayout_1.setStretch(1, 10)
        verticalLayout_1.setStretch(2, 50)
        verticalLayout_1.setStretch(3, 780)

        label_1 = QLabel()
        label_1.setText(u"Visualizaci\u00f3n de la Soluci\u00f3n")
        label_1.setFont(fuente)
        label_1.setMinimumSize(QSize(1200, 30))
        label_1.setAlignment(Qt.AlignCenter)
        verticalLayout_1.addWidget(label_1)

        line_1 = QFrame()
        line_1.setMinimumSize(QSize(1260, 1))
        line_1.setStyleSheet(u"background-color: rgb(255, 255, 255);")
        line_1.setFrameShadow(QFrame.Plain)
        line_1.setFrameShape(QFrame.HLine)
        verticalLayout_1.addWidget(line_1)
        
        # Creación del lienzo y de la barra de herramientas del mismo.
        self.MostrarSolucion = Lienzo(self)
        self.MostrarSolucion.setStyleSheet(u"background-color: rgb(255, 255, 255);")
        
        # La siguiente clase se crea para eliminar dos botones por defecto de la clase NavigationToolbar2QT. La necesidad de crear una clase para realizar esta modificación se basa en lo expuesto por torfbolt. (21 de marzo de 2013). Respuesta a la pregunta "How to modify the navigation toolbar easily in a matplotlib figure window?". stackoverflow. https://stackoverflow.com/a/15549675
        # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 3.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/3.0/
        class BarraHerramientasPersonalizada(NavigationToolbar):
            """Clase que contiene la barra de herramientas personalizada."""
            # Eliminación de los botones de "configuración de subgráficas" y "edición de ejes, curvas y parámetros de imagen".
            NavigationToolbar.toolitems.pop(-3)
            NavigationToolbar.toolitems.pop(-3)
        self.BarraHerramientas = BarraHerramientasPersonalizada(self.MostrarSolucion, ventana)
        self.BarraHerramientas.setStyleSheet(u"background-color:rgb(255, 255, 255); color:rgb(11, 61, 98); padding:10px;")
        self.BarraHerramientas.setMinimumSize(QSize(1000, 50))
        self.BarraHerramientas.setMaximumSize(QSize(1000, 60))
        self.BarraHerramientas.setVisible(False)
        self.BarraHerramientas.update()
        verticalLayout_1.addWidget(self.BarraHerramientas, alignment=Qt.AlignHCenter)
        verticalLayout_1.addWidget(self.MostrarSolucion)
        horizontalLayout_1.addWidget(frame2)

        line_2 = QFrame()
        line_2.setMinimumSize(QSize(5, 0))
        line_2.setFrameShadow(QFrame.Plain)
        line_2.setFrameShape(QFrame.VLine)
        horizontalLayout_1.addWidget(line_2)

        frame3 = QFrame()
        frame3.setSizePolicy(sizePolicy)
        frame3.setMinimumSize(QSize(560, 905))
        frame3.setMinimumSize(QSize(560, 905))
        frame3.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(246, 247, 247)")

        # Diseño del cuadro lateral derecho (herramientas).
        verticalLayout_2 = QVBoxLayout(frame3)
        verticalLayout_2.setSpacing(10)
        verticalLayout_2.setContentsMargins(0,0,0,0)
        verticalLayout_2.setStretch(0, 30)
        verticalLayout_2.setStretch(1, 20)
        verticalLayout_2.setStretch(2, 50)
        verticalLayout_2.setStretch(3, 80)
        verticalLayout_2.setStretch(4, 20)
        verticalLayout_2.setStretch(5, 30)
        verticalLayout_2.setStretch(6, 20)
        verticalLayout_2.setStretch(7, 50)
        verticalLayout_2.setStretch(8, 80)
        verticalLayout_2.setStretch(9, 20)
        verticalLayout_2.setStretch(10, 30)
        verticalLayout_2.setStretch(11, 20)
        verticalLayout_2.setStretch(12, 40)
        verticalLayout_2.setStretch(13, 40)
        verticalLayout_2.setStretch(14, 40)
        verticalLayout_2.setStretch(15, 40)
        verticalLayout_2.setStretch(16, 20)
        verticalLayout_2.setStretch(17, 50)

        label_2 = QLabel()
        label_2.setText(u"Coeficientes")
        label_2.setFont(fuente)
        label_2.setMinimumSize(QSize(510, 30))
        label_2.setMaximumSize(QSize(510, 30))
        label_2.setAlignment(Qt.AlignCenter)
        verticalLayout_2.addWidget(label_2, alignment=Qt.AlignHCenter)

        line_3 = QFrame()
        line_3.setMinimumSize(QSize(450, 1))
        line_3.setMaximumSize(QSize(450, 1))
        line_3.setStyleSheet(u"background-color: rgb(11, 61, 98);")
        line_3.setFrameShadow(QFrame.Sunken)
        line_3.setFrameShape(QFrame.HLine)
        verticalLayout_2.addWidget(line_3, alignment=Qt.AlignHCenter)

        horizontalLayout_2 = QHBoxLayout()
        horizontalLayout_2.setSpacing(0)
        horizontalLayout_2.setContentsMargins(0, 20, 0, 10)
        horizontalLayout_2.setStretch(0, 110)
        horizontalLayout_2.setStretch(1, 60)
        horizontalLayout_2.setStretch(2, 60)
        horizontalLayout_2.setStretch(3, 50)
        horizontalLayout_2.setStretch(4, 60)
        horizontalLayout_2.setStretch(5, 50)
        horizontalLayout_2.setStretch(4, 60)
        horizontalLayout_2.setStretch(5, 50)

        label_3 = QLabel()
        label_3.setText(u"Subproblema")
        label_3.setMinimumSize(QSize(100, 40))
        label_3.setMaximumSize(QSize(100, 40))
        label_3.setAlignment(Qt.AlignCenter)
        horizontalLayout_2.addWidget(label_3)

        # Diseño y configuración del QSpinBox para determinar el subproblema.
        self.Subproblema = QSpinBox()
        self.Subproblema.setMinimumSize(QSize(60, 40))
        self.Subproblema.setMaximumSize(QSize(60, 40))
        self.Subproblema.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(255, 255, 255)")
        self.Subproblema.setMinimum(1)
        horizontalLayout_2.addWidget(self.Subproblema)
        
        label_4 = QLabel()
        label_4.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "ValorPropioN.svg")))
        label_4.setMinimumSize(QSize(60, 40))
        label_4.setMaximumSize(QSize(60, 40))
        label_4.setAlignment(Qt.AlignCenter)
        horizontalLayout_2.addWidget(label_4)

        # Diseño y configuración del QSpinBox para determinar el primer indice de la doble suma en el subproblema (en caso de una única suma determina el indice de esta). Esto es equivalente a fijar el primer valor propio del subproblema.
        self.ValorPropio1 = QSpinBox()
        self.ValorPropio1.setMinimumSize(QSize(50, 40))
        self.ValorPropio1.setMaximumSize(QSize(50, 40))
        self.ValorPropio1.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(255, 255, 255)")
        horizontalLayout_2.addWidget(self.ValorPropio1)

        self.label_5 = QLabel()
        self.label_5.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "ValorPropioM.svg")))
        self.label_5.setMinimumSize(QSize(60, 40))
        self.label_5.setMaximumSize(QSize(60, 40))
        self.label_5.setAlignment(Qt.AlignCenter)
        horizontalLayout_2.addWidget(self.label_5)

        # Diseño y configuración del QSpinBox para determinar el segundo indice de la doble suma en el subproblema (en caso de que el subproblema tenga una doble suma como solución). Esto es equivalente a fijar el segundo valor propio del subproblema.
        self.ValorPropio2 = QSpinBox()
        self.ValorPropio2.setMinimumSize(QSize(50, 40))
        self.ValorPropio2.setMaximumSize(QSize(50, 40))
        self.ValorPropio2.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(255, 255, 255)")
        horizontalLayout_2.addWidget(self.ValorPropio2)

        self.label_5_1 = QLabel()
        self.label_5_1.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "ValorPropioL.svg")))
        self.label_5_1.setMinimumSize(QSize(60, 40))
        self.label_5_1.setMaximumSize(QSize(60, 40))
        self.label_5_1.setAlignment(Qt.AlignCenter)
        horizontalLayout_2.addWidget(self.label_5_1)

        # Diseño y configuración del QSpinBox para determinar el tercer indice de la triple suma en el subproblema (en caso de que el subproblema tenga una triple suma como solución). Esto es equivalente a fijar el tercer valor propio del subproblema.
        self.ValorPropio3 = QSpinBox()
        self.ValorPropio3.setMinimumSize(QSize(50, 40))
        self.ValorPropio3.setMaximumSize(QSize(50, 40))
        self.ValorPropio3.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(255, 255, 255)")
        horizontalLayout_2.addWidget(self.ValorPropio3)
        verticalLayout_2.addLayout(horizontalLayout_2)

        # Diseño y configuración del cuadro donde se muestra el coeficiente de la solución asociada a los valores propios especificados por los QSpinBoxes anteriores.
        self.ValoresCoeficienteView = QWebEngineView()
        self.ValoresCoeficienteView.setMinimumSize(QSize(480, 75))
        self.ValoresCoeficienteView.setMaximumSize(QSize(480, 75))
        self.pagina = self.ValoresCoeficienteView.page()
        self.html = html
        self.ValoresCoeficienteView.setHtml(self.html)
        self.pagina.runJavaScript('convert("{}");'.format("0"))
        verticalLayout_2.addWidget(self.ValoresCoeficienteView, alignment=Qt.AlignHCenter)

        line_4 = QFrame()
        line_4.setMinimumSize(QSize(550, 5))
        line_4.setMaximumSize(QSize(550, 5))
        line_4.setStyleSheet(u"background-color: rgb(11, 61, 98);")
        line_4.setFrameShadow(QFrame.Plain)
        line_4.setFrameShape(QFrame.HLine)
        verticalLayout_2.addWidget(line_4)

        label_6 = QLabel()
        label_6.setText(u"Solución")
        label_6.setFont(fuente)
        label_6.setMinimumSize(QSize(500, 30))
        label_6.setMaximumSize(QSize(500, 30))
        label_6.setAlignment(Qt.AlignCenter)
        verticalLayout_2.addWidget(label_6, alignment=Qt.AlignHCenter)

        line_5 = QFrame()
        line_5.setMinimumSize(QSize(450, 1))
        line_5.setMaximumSize(QSize(450, 1))
        line_5.setStyleSheet(u"background-color: rgb(11, 61, 98);")
        line_5.setFrameShadow(QFrame.Sunken)
        line_5.setFrameShape(QFrame.HLine)
        verticalLayout_2.addWidget(line_5, alignment=Qt.AlignHCenter)

        horizontalLayout_3 = QHBoxLayout()
        horizontalLayout_3.setSpacing(0)
        horizontalLayout_3.setContentsMargins(0, 20, 0, 10)
        horizontalLayout_3.setStretch(0, 60)
        horizontalLayout_3.setStretch(1, 70)
        horizontalLayout_3.setStretch(2, 60)
        horizontalLayout_3.setStretch(3, 70)
        horizontalLayout_3.setStretch(4, 60)
        horizontalLayout_3.setStretch(5, 70)

        self.label_7 = QLabel()
        self.label_7.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "x2.svg")))
        self.label_7.setMinimumSize(QSize(60, 40))
        self.label_7.setMaximumSize(QSize(60, 40))
        self.label_7.setAlignment(Qt.AlignCenter)
        horizontalLayout_3.addWidget(self.label_7)

        # Diseño y configuración del campo de entrada para ingresar el cuadro_fijo de la primera coordenada en donde se evaluará la solución obtenida.
        self.Coordenada1 = QLineEdit()
        self.Coordenada1.setText("0")
        self.Coordenada1.setMinimumSize(QSize(70, 40))
        self.Coordenada1.setMaximumSize(QSize(70, 40))
        self.Coordenada1.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(255, 255, 255)")
        self.Coordenada1.textEdited.connect(lambda: self.calcularValorSolucion())
        horizontalLayout_3.addWidget(self.Coordenada1)

        self.label_8 = QLabel()
        self.label_8.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "y2.svg")))
        self.label_8.setMinimumSize(QSize(60, 40))
        self.label_8.setMaximumSize(QSize(60, 40))
        self.label_8.setAlignment(Qt.AlignCenter)
        horizontalLayout_3.addWidget(self.label_8)

        # Diseño y configuración del campo de entrada para ingresar el cuadro_fijo de la segunda coordenada en donde se evaluará la solución obtenida.
        self.Coordenada2 = QLineEdit()
        self.Coordenada2.setText("0")
        self.Coordenada2.setMinimumSize(QSize(70, 40))
        self.Coordenada2.setMaximumSize(QSize(70, 40))
        self.Coordenada2.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(255, 255, 255)")
        self.Coordenada2.textEdited.connect(lambda: self.calcularValorSolucion())
        horizontalLayout_3.addWidget(self.Coordenada2)

        self.label_9 = QLabel()
        self.label_9.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "z2.svg")))
        self.label_9.setMinimumSize(QSize(60, 40))
        self.label_9.setMaximumSize(QSize(60, 40))
        self.label_9.setAlignment(Qt.AlignCenter)
        horizontalLayout_3.addWidget(self.label_9)

        # Diseño y configuración del campo de entrada para ingresar el cuadro_fijo de la tercera coordenada en donde se evaluará la solución obtenida.
        self.Coordenada3 = QLineEdit()
        self.Coordenada3.setText("0")
        self.Coordenada3.setMinimumSize(QSize(70, 40))
        self.Coordenada3.setMaximumSize(QSize(70, 40))
        self.Coordenada3.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(255, 255, 255)")
        self.Coordenada3.textEdited.connect(lambda: self.calcularValorSolucion())
        horizontalLayout_3.addWidget(self.Coordenada3)
        verticalLayout_2.addLayout(horizontalLayout_3)
            
        # Diseño y configuración del cuadro donde se muestra el cuadro_fijo de la solución en el punto especificado por los tres QSpinBoxes anteriores.
        self.Valorview = QWebEngineView()
        self.Valorview.setMinimumSize(QSize(480, 75))
        self.Valorview.setMaximumSize(QSize(480, 75))
        self.pagina2 = self.Valorview.page()
        self.Valorview.setHtml(self.html)
        self.pagina2.runJavaScript('convert("{}");'.format("0"))
        self.pagina2.loadFinished.connect(lambda: self.calcularValorSolucion())
        verticalLayout_2.addWidget(self.Valorview, alignment=Qt.AlignHCenter)

        line_6 = QFrame()
        line_6.setMinimumSize(QSize(550, 5))
        line_6.setMaximumSize(QSize(550, 5))
        line_6.setStyleSheet(u"background-color: rgb(11, 61, 98);")
        line_6.setFrameShadow(QFrame.Plain)
        line_6.setFrameShape(QFrame.HLine)
        verticalLayout_2.addWidget(line_6)

        label_10 = QLabel()
        label_10.setText(u"Visualización")
        label_10.setFont(fuente)
        label_10.setMinimumSize(QSize(500, 30))
        label_10.setMaximumSize(QSize(500, 30))
        label_10.setAlignment(Qt.AlignCenter)
        verticalLayout_2.addWidget(label_10, alignment=Qt.AlignHCenter)

        self.line_7 = QFrame()
        self.line_7.setMinimumSize(QSize(450, 1))
        self.line_7.setMaximumSize(QSize(450, 1))
        self.line_7.setStyleSheet(u"background-color: rgb(11, 61, 98);")
        self.line_7.setFrameShadow(QFrame.Plain)
        self.line_7.setFrameShape(QFrame.HLine)
        verticalLayout_2.addWidget(self.line_7, alignment=Qt.AlignHCenter)

        horizontalLayout_4 = QHBoxLayout()
        horizontalLayout_4.setContentsMargins(10, 20, 10, 10)
        horizontalLayout_4.setSpacing(5)
        horizontalLayout_4.setStretch(0, 20)
        horizontalLayout_4.setStretch(1, 260)
        horizontalLayout_4.setStretch(2, 180)

        # Diseño y configuración de la casilla de cálculo automático de valores para las curvas de nivel.
        self.CurvasNivelAuto = QCheckBox()
        self.CurvasNivelAuto.setText("")
        self.CurvasNivelAuto.setMinimumSize(QSize(20, 40))
        self.CurvasNivelAuto.setMaximumSize(QSize(20, 40))
        self.CurvasNivelAuto.setShortcut("Ctrl+A")
        horizontalLayout_4.addWidget(self.CurvasNivelAuto, alignment=Qt.AlignHCenter)

        self.label_11 = QLabel()
        self.label_11.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(246, 247, 247)")
        self.label_11.setText("Curvas de Nivel Automáticas")
        self.label_11.setMinimumSize(QSize(260, 30))
        self.label_11.setMaximumSize(QSize(260, 30))
        self.label_11.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        horizontalLayout_4.addWidget(self.label_11)

        # Diseño y configuración de la casilla de proyección de la gráfica.
        self.ProyeccionEntrada = QCheckBox()
        self.ProyeccionEntrada.setText("Proyección 2D")
        self.ProyeccionEntrada.setStyleSheet(u"spacing:20px")
        self.ProyeccionEntrada.setMinimumSize(QSize(180, 40))
        self.ProyeccionEntrada.setMaximumSize(QSize(180, 40))
        self.ProyeccionEntrada.setShortcut("Ctrl+p")
        self.ProyeccionEntrada.stateChanged.connect(lambda: self.signals.proyeccion_signal.emit())
        horizontalLayout_4.addWidget(self.ProyeccionEntrada, alignment=Qt.AlignHCenter)
        verticalLayout_2.addLayout(horizontalLayout_4)

        horizontalLayout_5 = QHBoxLayout()
        horizontalLayout_5.setContentsMargins(10, 10, 10, 10)
        horizontalLayout_5.setSpacing(5)
        horizontalLayout_5.setStretch(0, 20)
        horizontalLayout_5.setStretch(1, 220)
        horizontalLayout_5.setStretch(2, 120)
        horizontalLayout_5.setStretch(3, 10)
        horizontalLayout_5.setStretch(4, 80)

        # Diseño y configuración de la casilla, el campo de entrada y el botón para el ingreso manual de valores para las curvas de nivel.
        self.CurvasNivelEspecificas = QCheckBox()
        self.CurvasNivelEspecificas.setText("")
        self.CurvasNivelEspecificas.setStyleSheet(u"spacing:0px")
        self.CurvasNivelEspecificas.setMinimumSize(QSize(20, 40))
        self.CurvasNivelEspecificas.setMinimumSize(QSize(20, 40))
        self.CurvasNivelEspecificas.setShortcut("Ctrl+E")
        horizontalLayout_5.addWidget(self.CurvasNivelEspecificas, alignment=Qt.AlignHCenter)

        self.label_12 = QLabel()
        self.label_12.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(246, 247, 247)")
        self.label_12.setText("Curvas de Nivel Específicas")
        self.label_12.setMinimumSize(QSize(220, 30))
        self.label_12.setMaximumSize(QSize(220, 30))
        self.label_12.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        horizontalLayout_5.addWidget(self.label_12)

        self.CurvasNivelEspecificasEntrada = QLineEdit()
        self.CurvasNivelEspecificasEntrada.setMinimumSize(QSize(120, 40))
        self.CurvasNivelEspecificasEntrada.setMaximumSize(QSize(120, 40))
        self.CurvasNivelEspecificasEntrada.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(255, 255, 255)")
        horizontalLayout_5.addWidget(self.CurvasNivelEspecificasEntrada, alignment=Qt.AlignLeft)

        label_13 = QLabel()
        label_13.setText("")
        label_13.setMinimumSize(QSize(10, 40))
        label_13.setMaximumSize(QSize(10, 40))
        horizontalLayout_5.addWidget(label_13)

        self.GraficarCurvasFija = QPushButton(frame3, clicked = lambda: self.interpretacionCurvasNivel())
        self.GraficarCurvasFija.setMaximumSize(QSize(80, 40))
        self.GraficarCurvasFija.setMinimumSize(QSize(80, 40))
        self.GraficarCurvasFija.setText("Ir")
        self.GraficarCurvasFija.setStyleSheet(u"color: rgba(246, 247, 247, 255); background-color: rgb(11, 61, 98)")
        horizontalLayout_5.addWidget(self.GraficarCurvasFija)
        verticalLayout_2.addLayout(horizontalLayout_5)

        # Configuración de las casillas de cálculo automático e ingreso manual de valores para las curvas de nivel como botones mutuamente excluyentes.
        self.Grupo = QButtonGroup()
        self.Grupo.addButton(self.CurvasNivelAuto, 1)
        self.Grupo.addButton(self.CurvasNivelEspecificas, 2)
        self.Grupo.setExclusive(True)
        self.Grupo.buttonPressed.connect(self.activarCurvas)
        self.Grupo.buttonClicked.connect(lambda: self.signals.curvas_signal.emit())
        self.CurvasNivelAuto.setShortcut("Ctrl+A")
        
        # Diseño y configuración de las casillas de determinación de coordenada fija.
        horizontalLayout_6 = QHBoxLayout()
        horizontalLayout_6.setSpacing(1)
        horizontalLayout_6.setContentsMargins(0, 10, 0, 10)
        horizontalLayout_6.setStretch(0, 120)
        horizontalLayout_6.setStretch(1, 10)
        horizontalLayout_6.setStretch(2, 20)
        horizontalLayout_6.setStretch(3, 30)
        horizontalLayout_6.setStretch(4, 20)
        horizontalLayout_6.setStretch(5, 30)
        horizontalLayout_6.setStretch(6, 20)
        horizontalLayout_6.setStretch(7, 30)

        self.label_14 = QLabel()
        self.label_14.setText("Coordenada Fija")
        self.label_14.setMinimumSize(QSize(120, 40))
        self.label_14.setMaximumSize(QSize(120, 40))
        horizontalLayout_6.addWidget(self.label_14)

        self.line_8 = QFrame()
        self.line_8.setMinimumSize(QSize(1, 40))
        self.line_8.setMaximumSize(QSize(1, 40))
        self.line_8.setStyleSheet(u"background-color: rgb(11, 61, 98);")
        self.line_8.setFrameShadow(QFrame.Plain)
        self.line_8.setFrameShape(QFrame.VLine)
        horizontalLayout_6.addWidget(self.line_8)

        self.CoordenadaFija_1 = QCheckBox()
        self.CoordenadaFija_1.setChecked(True)
        self.CoordenadaFija_1.setText("")
        self.CoordenadaFija_1.setStyleSheet(u"color: rgb(255, 255, 255); background-color: rgb(246, 247, 247)")
        self.CoordenadaFija_1.setMinimumSize(QSize(20, 40))
        self.CoordenadaFija_1.setMaximumSize(QSize(20, 40))
        horizontalLayout_6.addWidget(self.CoordenadaFija_1)

        self.CoordenadaFija_1_label = QLabel()
        self.CoordenadaFija_1_label.setMinimumSize(QSize(30, 40))
        self.CoordenadaFija_1_label.setMaximumSize(QSize(30, 40))
        self.CoordenadaFija_1_label.setAlignment(Qt.AlignCenter)
        horizontalLayout_6.addWidget(self.CoordenadaFija_1_label)

        self.CoordenadaFija_2 = QCheckBox()
        self.CoordenadaFija_2.setText("")
        self.CoordenadaFija_2.setStyleSheet(u"color: rgb(255, 255, 255); background-color: rgb(246, 247, 247)")
        self.CoordenadaFija_2.setMinimumSize(QSize(20, 40))
        self.CoordenadaFija_2.setMaximumSize(QSize(20, 40))
        horizontalLayout_6.addWidget(self.CoordenadaFija_2)

        self.CoordenadaFija_2_label = QLabel()
        self.CoordenadaFija_2_label.setMinimumSize(QSize(30, 40))
        self.CoordenadaFija_2_label.setMaximumSize(QSize(30, 40))
        self.CoordenadaFija_2_label.setAlignment(Qt.AlignCenter)
        horizontalLayout_6.addWidget(self.CoordenadaFija_2_label)

        self.CoordenadaFija_3 = QCheckBox()
        self.CoordenadaFija_3.setText("")
        self.CoordenadaFija_3.setStyleSheet(u"color: rgb(255, 255, 255); background-color: rgb(246, 247, 247)")
        self.CoordenadaFija_3.setMinimumSize(QSize(20, 40))
        self.CoordenadaFija_3.setMaximumSize(QSize(20, 40))
        horizontalLayout_6.addWidget(self.CoordenadaFija_3)

        self.CoordenadaFija_3_label = QLabel()
        self.CoordenadaFija_3_label.setMinimumSize(QSize(30, 40))
        self.CoordenadaFija_3_label.setMaximumSize(QSize(30, 40))
        self.CoordenadaFija_3_label.setAlignment(Qt.AlignCenter)
        horizontalLayout_6.addWidget(self.CoordenadaFija_3_label)
        verticalLayout_2.addLayout(horizontalLayout_6)

        # Configuración de las casillas de coordenadas fijas como casillas mutuamente excluyentes.
        self.CoordenadaFija_Casilla = QButtonGroup()
        self.CoordenadaFija_Casilla.addButton(self.CoordenadaFija_1, 1)
        self.CoordenadaFija_Casilla.addButton(self.CoordenadaFija_2, 2)
        self.CoordenadaFija_Casilla.addButton(self.CoordenadaFija_3, 3)
        self.CoordenadaFija_Casilla.setExclusive(True)
        self.CoordenadaFija_Casilla.buttonClicked.connect(lambda: self.signals.coordenada_signal.emit())

        horizontalLayout_7 = QHBoxLayout()
        horizontalLayout_7.setSpacing(1)
        horizontalLayout_7.setContentsMargins(0, 10, 0, 10)
        horizontalLayout_7.setStretch(0, 180)
        horizontalLayout_7.setStretch(1, 100)
        horizontalLayout_7.setStretch(2, 80)

        self.label_15 = QLabel()
        self.label_15.setText("Valor Coordenada Fija")
        self.label_15.setMinimumSize(QSize(180, 40))
        self.label_15.setMaximumSize(QSize(180, 40))
        self.label_15.setAlignment(Qt.AlignCenter)
        horizontalLayout_7.addWidget(self.label_15)

        # Diseño y configuración del campo de entrada del cuadro_fijo de la coordenada fija y el botón de graficación correspondiente.
        self.CoordenadaFija = QLineEdit()
        self.CoordenadaFija.setMinimumSize(QSize(100, 40))
        self.CoordenadaFija.setMaximumSize(QSize(100, 40))
        self.CoordenadaFija.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(255, 255, 255)")
        horizontalLayout_7.addWidget(self.CoordenadaFija)

        self.GraficarCoordenadaFija = QPushButton(frame3, clicked = lambda: self.signals.corte_signal.emit())
        self.GraficarCoordenadaFija.setMaximumSize(QSize(80, 40))
        self.GraficarCoordenadaFija.setMinimumSize(QSize(80, 40))
        self.GraficarCoordenadaFija.setText("Ir")
        self.GraficarCoordenadaFija.setStyleSheet(u"color: rgba(246, 247, 247, 255); background-color: rgb(11, 61, 98)")
        horizontalLayout_7.addWidget(self.GraficarCoordenadaFija)
        verticalLayout_2.addLayout(horizontalLayout_7)

        line_9 = QFrame()
        line_9.setMinimumSize(QSize(550, 5))
        line_9.setMaximumSize(QSize(550, 5))
        line_9.setStyleSheet(u"background-color: rgb(11, 61, 98);")
        line_9.setFrameShadow(QFrame.Plain)
        line_9.setFrameShape(QFrame.HLine)
        verticalLayout_2.addWidget(line_9)
    
        # Diseño y configuración del botón de guardado de animación.
        self.GuardarAnimacion = QPushButton(frame3, clicked = lambda: self.signals.guardar_signal.emit())
        self.GuardarAnimacion.setText(u"Guardar Animaci\u00f3n")
        self.GuardarAnimacion.setMinimumSize(QSize(400, 45))
        self.GuardarAnimacion.setMaximumSize(QSize(400, 45))
        self.GuardarAnimacion.setShortcut("Ctrl+S")
        self.GuardarAnimacion.setDisabled(True)
        self.GuardarAnimacion.setStyleSheet("background-color: rgb(127,146,151); color: rgb(234,237,239);")
        verticalLayout_2.addWidget(self.GuardarAnimacion, alignment=Qt.AlignCenter)
        horizontalLayout_1.addWidget(frame3)

        # Inicialización de las variables auxiliares.
        self.curvasdibujadas = False
        self.curvasdibujadas2 = False
        self.valorpropiodependendiente = ""
        self.modificado = False
        self.inicio = True
        self.etiquetas = False
        self._ready = False
        self.carga = False
        self.valorespecial = False
        self.valorerroneo = False
        self.curvas = False
        self.dependencia_tiempo = False
        self.EmergenteVentanaGraficacion = QMessageBox()

        QMetaObject.connectSlotsByName(ventana)

    def transferirDatos(self, funcion, soluciones, numero_terminos, valores, dominio, simbolos, colormap, proyeccion, coordenadas, numero_subproblemas, precision, calidad, particiones, dependencia, bidependencia, indicesdependencia, invertir, valorespropios):
        """
        Transfiere datos desde la ventana principal a esta ventana.

        Parámetros
        ----------
        **funcion** : Funcion obtenida a través del comando de Sympy 'lambdify'
            Solución representada como una función de numpy.

        **soluciones** : Expresiones de Sympy
            Subsoluciones de cada subproblema.

        **numero_terminos** : lista (unidimensional o bidimensional, dependiendo de si se tiene una suma simple o una doble suma, respectivamente) de enteros
            Lista que contiene los límites de las sumas.

        **valores** : arreglo bidimensional o tridimensional de números flotantes
            Valores de la solución en puntos específicos del dominio del problema.

        **dominio** : lista que contiene a lo más tres listas de números flotantes (cada una de longitud dos)
            Extremos de los dominios de cada una de las coordenadas de la solución.

        **simbolos** : lista de símbolos de Sympy
            Símbolos de las coordenadas de la solución.

        **colormap** : mapa de color de matplotlib
            Mapa de color para la gráfica.

        **proyeccion** : bool
            Valor booleano que determina la proyección de la gráfica (visualizacion tridimensional o bidimensional en problemas de tres o dos coordenadas y visualizacion unidimensional o bidimensional en problemas de dos dimensiones con dependencia temporal.)

        **coordenadas** : string
            Sistema de coordenadas de la solución.

        **numero_subproblemas** : entero
            Numero de subproblemas ingresados.
        
        **precision** : entero
            Precisión decimal de los números flotantes.

        **calidad** : bool
            Determina calidad alta (True) o calidad media (False).

        **particiones** : lista de listas de números flotantes
            Determina las particiones de los dominios de las coordenadas.

        **depedencia** : bool
            Indica si algunos de los conjuntos de valores propios de un subproblema están ligados.

        **bidepedencia** : bool
            Indica si todos los conjuntos de valores propios de un subproblema están ligados.

        **indicesdepedencia** : lista de números enteros
            Indica los subproblemas en donde los valores propios están ligados.

        **invertir** : bool
            Indica si el primer conjunto de valores propios depende del segundo (False) o viceversa (True).

        **valorespropios: arreglo de números flotantes
            Contiene los valores propios calculados.
        """

        self.Funcion = funcion
        self.Soluciones = soluciones
        self.NumeroTerminos = numero_terminos
        self.MatrizResultados = valores
        self.Dominio = dominio
        self.Simbolos = simbolos
        self.Colormap = colormap
        self.Proyeccion = proyeccion
        self.Coordenadas = coordenadas
        self.NumeroSubproblemas = numero_subproblemas
        self.Precision = precision
        self.Calidad = calidad
        self.Dominios = particiones
        self.dependencia = dependencia
        self.bidependencia = bidependencia
        self.indicesdependencia = indicesdependencia
        self.invertir = invertir
        self.ValoresPropios = valorespropios
        
        self.valorpropiodependendiente = ""

        if len(self.Dominio[-1]) == 1:
            self.dependencia_tiempo = True
        else:
            self.dependencia_tiempo = False

    def editarOpciones(self):
        self.envioActualizacion("Habilitando Herramientas")

        print(self.Dominio, self.NumeroTerminos[0])

        try:
            # Diseño de la caja de herramientas para la visualización de los coeficientes de cada subsolución.
            self.Subproblema.setMaximum(int(self.NumeroSubproblemas))
            self.ValorPropio1.setMaximum(int(self.NumeroTerminos[0][0][1]))
            self.ValorPropio1.setMinimum(int(self.NumeroTerminos[0][0][0]))
            if len(self.NumeroTerminos[0]) > 1:
                sizePolicy2 = self.ValorPropio1.sizePolicy()
                sizePolicy2.setRetainSizeWhenHidden(True)
                # Cuando hay más de un conjunto de valores propios en el subproblema 1.
                if self.NumeroTerminos[0][1][0] == "-n":
                    self.ValorPropio2.setMaximum(int(self.NumeroTerminos[0][0][0]))
                    self.ValorPropio2.setMinimum(-int(self.NumeroTerminos[0][0][0]))
                else:
                    self.ValorPropio2.setMaximum(int(self.NumeroTerminos[0][1][1]))
                    self.ValorPropio2.setMinimum(int(self.NumeroTerminos[0][1][0]))

                if len(self.NumeroTerminos[0]) == 3:
                    # Cuando hay más de dos conjuntos de valores propios en el subproblema 1.
                    if self.NumeroTerminos[0][2][0] == "-n":
                        self.ValorPropio3.setMaximum(int(self.NumeroTerminos[0][1][0]))
                        self.ValorPropio3.setMinimum(-int(self.NumeroTerminos[0][1][0]))
                    else:
                        self.ValorPropio3.setMaximum(int(self.NumeroTerminos[0][2][1]))
                        self.ValorPropio3.setMinimum(int(self.NumeroTerminos[0][2][0]))
                else:
                    self.ValorPropio3.setRange(0, 10)
                    self.ValorPropio3.setSpecialValueText("")
                    self.ValorPropio3.setValue(0)
                    self.ValorPropio3.setEnabled(False)
                    self.label_5_1.setEnabled(False)
                    self.ValorPropio3.setStyleSheet(u"color: rgba(11, 61, 98, 0.9); background-color: rgba(255, 255, 255, 0.9); border-color: rgba(255, 255, 255, 0.9)")
                    self.ValorPropio3.setSizePolicy(sizePolicy2)
                    self.ValorPropio3.setVisible(False)
                    self.label_5_1.setSizePolicy(sizePolicy2)
                    self.label_5_1.setVisible(False)
            else: 
                # Cuando solo hay un conjunto de valores propios en el subproblema 1.
                self.ValorPropio2.setRange(0, 10)
                self.ValorPropio2.setSpecialValueText("")
                self.ValorPropio2.setValue(0)
                self.ValorPropio2.setEnabled(False)
                self.label_5.setEnabled(False)
                self.ValorPropio2.setStyleSheet(u"color: rgba(11, 61, 98, 0.9); background-color: rgba(255, 255, 255, 0.9); border-color: rgba(255, 255, 255, 0.9)")
                sizePolicy2 = self.ValorPropio2.sizePolicy()
                sizePolicy2.setRetainSizeWhenHidden(True)
                self.ValorPropio2.setSizePolicy(sizePolicy2)
                self.ValorPropio2.setVisible(False)
                self.label_5.setSizePolicy(sizePolicy2)
                self.label_5.setVisible(False)

                self.ValorPropio3.setRange(0, 10)
                self.ValorPropio3.setSpecialValueText("")
                self.ValorPropio3.setValue(0)
                self.ValorPropio3.setEnabled(False)
                self.label_5_1.setEnabled(False)
                self.ValorPropio3.setStyleSheet(u"color: rgba(11, 61, 98, 0.9); background-color: rgba(255, 255, 255, 0.9); border-color: rgba(255, 255, 255, 0.9)")
                self.ValorPropio3.setSizePolicy(sizePolicy2)
                self.ValorPropio3.setVisible(False)
                self.label_5_1.setSizePolicy(sizePolicy2)
                self.label_5_1.setVisible(False)

            print("a")
            # Diseño de la caja de herramientas para la visualización del valor de la solución en un punto determinado.
            self.Coordenada1.setText("{}".format(self.Dominio[0][0]))
            if not self.dependencia_tiempo:
                self.Coordenada2.setText("{}".format(self.Dominio[1][0]))
            else:
                self.Coordenada2.setText("0")

            print("a")
            if len(self.Dominio) < 3:
                # Cuando solo hay dos variables en la solución.
                self.Coordenada3.setEnabled(False)
                self.label_9.setEnabled(False)
                self.label_9.setSizePolicy(sizePolicy2)
                self.label_9.setVisible(False)
                self.Coordenada3.setSizePolicy(sizePolicy2)
                self.Coordenada3.setVisible(False)
                self.Coordenada3.setStyleSheet(u"color: rgba(11, 61, 98, 0.9); background-color: rgba(255, 255, 255, 0.9); border-color: rgba(255, 255, 255, 0.9)")
            else:
                if not self.Coordenada3.isEnabled():
                    self.Coordenada3.setEnabled(True)
                    self.label_9.setEnabled(True)
                    self.label_9.setSizePolicy(sizePolicy2)
                    self.label_9.setVisible(True)
                    self.Coordenada3.setSizePolicy(sizePolicy2)
                    self.Coordenada3.setVisible(True)
                    self.Coordenada3.setStyleSheet(u"color: rgba(11, 61, 98, 255); background-color: rgba(255, 255, 255, 0.9); border-color: rgba(255, 255, 255, 255)")
                if not self.dependencia_tiempo:
                    # En caso de que la tercera variable sea espacial.
                    self.Coordenada3.setText("{}".format(self.Dominio[-1][0]))
                else:
                    # Cuando la tercera variable es temporal.
                    self.Coordenada3.setText("0")

            print("a")
            # Colocación de las imágenes de cada una de las variables (coordenadas) involucradas.
            if self.Coordenadas == "Cartesianas":
                self.label_7.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "x2.svg")))
                self.label_8.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "y2.svg")))
                self.label_9.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "z2.svg")))
            elif self.Coordenadas == "Cilíndricas / Polares":
                self.label_7.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "r2.svg")))
                self.label_8.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "phi2.svg")))
                self.label_9.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "z2.svg")))
            elif self.Coordenadas == "Esféricas":
                self.label_7.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "r2.svg")))
                self.label_8.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "theta2.svg")))
                self.label_9.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "phi2.svg")))
            if len(self.Dominio) == 2 and len(self.Dominio[-1]) == 1:
                self.label_8.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "t2.svg")))
                self.label_9.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "sinOpcion.svg")))
            elif len(self.Dominio) == 3 and len(self.Dominio[-1]) == 1:
                self.label_9.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "t2.svg")))
            elif len(self.Dominio) == 2 and len(self.Dominio[-1]) != 1:
                self.label_9.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "sinOpcion.svg")))
            
            print("a")
            # Diseño de la caja de herramientas para la visualización de curvas de nivel, intercambio de proyecciones y graficación de cortes específicos.
            if ((len(self.Dominio) == 3) and not self.dependencia_tiempo) or ((len(self.Dominio) == 2) and self.dependencia_tiempo):
                # Desactivación de curvas de nivel cuando no hay dependencia temporal y se tiene una visualización 3D de una función de 3 variables espaciales o cuando se tiene un problema de una dimensión espacial con dependencia temporal.
                self.CurvasNivelAuto.setCheckable(False)
                self.CurvasNivelAuto.setEnabled(False)
                self.CurvasNivelEspecificas.setCheckable(False)
                self.CurvasNivelEspecificas.setEnabled(False)
                self.CurvasNivelEspecificasEntrada.setDisabled(True)
                self.GraficarCurvasFija.setDisabled(True)
                self.GraficarCurvasFija.setStyleSheet("background-color: rgb(127,146,151); color: rgb(234,237,239);")
            if self.Proyeccion:
                # Si se activó la proyección desde la pantalla principal de la app, se selecciona esta opción en la graficación.
                self.ProyeccionEntrada.setChecked(True)
            # Colocación de las imágenes de cada una de las variables (coordenadas) posibles para realizar la graficación de un corte específico.
            if self.Coordenadas == "Cartesianas":
                self.CoordenadaFija_1_label.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "x2.svg")))
                self.CoordenadaFija_2_label.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "y2.svg")))
                self.CoordenadaFija_3_label.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "z2.svg")))
            elif self.Coordenadas == "Cilíndricas / Polares":
                self.CoordenadaFija_1_label.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "r2.svg")))
                self.CoordenadaFija_2_label.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "phi2.svg")))
                self.CoordenadaFija_3_label.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "z2.svg")))
            elif self.Coordenadas == "Esféricas":
                self.CoordenadaFija_1_label.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "r2.svg")))
                self.CoordenadaFija_2_label.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "theta2.svg")))
                self.CoordenadaFija_3_label.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "phi2.svg")))
            self.CoordenadaFija_1.setSizePolicy(sizePolicy2)
            self.CoordenadaFija_2.setSizePolicy(sizePolicy2)
            self.CoordenadaFija_3.setSizePolicy(sizePolicy2)
            print("a")
            if (len(self.Dominio) < 3) and (not self.dependencia_tiempo):
                # Cuando se tiene un problema de dos coordenadas y estas son espaciales, se deshabilita la opción de graficación de cortes.
                self.CoordenadaFija_1.setChecked(False)
                self.CoordenadaFija_1.setEnabled(False)
                self.CoordenadaFija_2.setEnabled(False)
                self.CoordenadaFija_3.setEnabled(False)
                self.CoordenadaFija_1.setVisible(False)
                self.CoordenadaFija_2.setVisible(False)
                self.CoordenadaFija_3.setVisible(False)
                self.CoordenadaFija_1_label.setEnabled(False)
                self.CoordenadaFija_2_label.setEnabled(False)
                self.CoordenadaFija_3_label.setEnabled(False)
                self.CoordenadaFija_1_label.setVisible(False)
                self.CoordenadaFija_2_label.setVisible(False)
                self.CoordenadaFija_3_label.setVisible(False)
                self.CoordenadaFija.setEnabled(False)
                self.CoordenadaFija.setVisible(False)
                self.CoordenadaFija.setText("{}".format(float(self.Dominio[0][0])))
                self.CoordenadaFija.setSizePolicy(sizePolicy2)
                self.label_14.setEnabled(False)
                self.label_14.setSizePolicy(sizePolicy2)
                self.label_14.setVisible(False)
                self.line_8.setSizePolicy(sizePolicy2)
                self.line_8.setVisible(False)
                self.line_8.setEnabled(False)
                self.label_15.setEnabled(False)
                self.label_15.setSizePolicy(sizePolicy2)
                self.label_15.setVisible(False)
                self.GraficarCoordenadaFija.setEnabled(False)
                self.GraficarCoordenadaFija.setVisible(False)
                self.GraficarCoordenadaFija.setSizePolicy(sizePolicy2)
                self.CurvasNivelAuto.setCheckable(True)
                self.CurvasNivelAuto.setShortcut("Ctrl+A")
                self.CurvasNivelEspecificas.setCheckable(True)
            elif self.dependencia_tiempo:
                # Cuando se tiene dependencia temporal, solo se pueden graficar cortes temporales.
                self.CoordenadaFija_2.setSizePolicy(sizePolicy2)
                self.CoordenadaFija_3.setSizePolicy(sizePolicy2)
                self.CoordenadaFija_2.setEnabled(False)
                self.CoordenadaFija_3.setEnabled(False)
                self.CoordenadaFija_2.setVisible(False)
                self.CoordenadaFija_3.setVisible(False)
                self.CoordenadaFija_2_label.setEnabled(False)
                self.CoordenadaFija_3_label.setEnabled(False)
                self.CoordenadaFija_1_label.setPixmap(QPixmap(os.path.join(directorio_base, "Iconos", "t2.svg")))
                self.CoordenadaFija_2_label.setVisible(False)
                self.CoordenadaFija_3_label.setVisible(False)
                if self.Proyeccion or (len(self.Dominio) > 2):
                    self.CurvasNivelAuto.setShortcut("Ctrl+A")
                    self.CurvasNivelAuto.setEnabled(True)
            else:
                # En otro caso, tres coordenadas espaciales, se activa el corte en la primera coordenada.
                self.CoordenadaFija_1.setChecked(True)
        except:
            # Interpretación del tipo de error.
            tipoError, explicacion, line = sys.exc_info()[:3]
            print(tipoError)
            print(explicacion)
            print(line.tb_lineno)

    def crearGrafica(self):
        self.envioActualizacion("Habilitando Lienzo")

        # Habilitación del lienzo y la barra de herramientas.
        self.BarraHerramientas.setVisible(True)
        self.MostrarSolucion.figura.set_visible(True)
        self.MostrarSolucion.figura.clear()
        self.MostrarSolucion.figura.canvas.draw_idle()

        self.envioActualizacion("Calculando Máximos y Mínimos")

        # Determinación del máximo y mínimo.
        self.minimo = self.MatrizResultados.min()
        self.maximo = self.MatrizResultados.max()
        if self.minimo == self.maximo:
            if self.minimo != 0:
                self.minimo = self.MatrizResultados.min()-self.MatrizResultados.min()*0.1
                self.maximo = self.MatrizResultados.max()+self.MatrizResultados.max()*0.1
            else: 
                self.minimo = -0.5
                self.maximo = 0.5

        self.graficacion()

    def graficacion(self, curvas_nivel = False, casilla = None, coordenada_especifica = None):
        """
        Crea la gráfica y, en su caso, inicializa la animación de la gráfica.

        Parámetros
        ----------
        curvas_nivel: bool, False es el cuadro_fijo predeterminado
            Determina si la gráfica mostrará las curvas de nivel o no.

        casilla: QCheckBox, None es el cuadro_fijo predeterminado
            Guarda la casilla de curvas de nivel que se encuentra marcada.

        coordenada_especifica: string, None es el cuadro_fijo predeterminado 
            Coordenada fija en la graficación (solo para problemas con tres dimensiones).
        """

        if curvas_nivel == True:
            # Parámetros cuando se requieren las curvas de nivel.
            self.curvas = True
            self.casilla = casilla
            self.funcion_curvas = self.interpretacionCurvasNivel
        else:
            # Parámetros cuando no se requieren las curvas de nivel.
            self.curvas = False
            self.casilla = None
            self.funcion_curvas = None
        
        self.envioActualizacion("Construyendo Grafica")

        # Creación de la gráfica.
        if self.Proyeccion:
            # Cuando se quiere graficar la proyección.
            if (len(self.Dominio) == 2) and (len(self.Dominio[-1]) == 1):
                # Para problemas de una dimensión espacial y con dependencia temporal.
                self.DatosGrafica = self.crearProyeccion1D(self.MostrarSolucion)
                self.Valores = self.MatrizResultados
                self.Animacion = ReproductorProyeccion1D(self.MostrarSolucion, self.introducirProyeccion1D, fargs=[*self.DatosGrafica, self.MatrizResultados, self.MostrarSolucion.axes, self.Cota, self.Colormap, self.GuardarAnimacion], interval = 1000/self.DatosGrafica[-1], maximo = int(self.DatosGrafica[-2]*self.DatosGrafica[-1]))
            elif (len(self.Dominio) == 2) or (len(self.Dominio[-1]) == 1):
                # Para problemas de dos dimensiones espaciales con o sin dependencia temporal.
                self.Valores = self.MatrizResultados
                if self.Coordenadas == "Cartesianas":
                    self.DatosGrafica = self.crearProyeccion2D_cartesianas(self.MostrarSolucion)
                elif self.Coordenadas == "Cilíndricas / Polares":
                    self.DatosGrafica = self.crearProyeccion2D_polares(self.MostrarSolucion)
                if self.dependencia_tiempo:
                    self.Animacion = ReproductorGeneral(self.MostrarSolucion, self.actualizarProyeccion2D, fargs=[int(len(self.DatosGrafica[0])/10), *self.DatosGrafica, self.Coordenadas, self.Valores, self.MostrarSolucion.axes, self.Cota, self.Colormap, self.GuardarAnimacion], maximo = int(len(self.DatosGrafica[0])/10+self.DatosGrafica[-2]*self.DatosGrafica[-1]+1), interval = 1000/self.DatosGrafica[-1], curvas_nivel =self.curvas, funcion_curvas = self.funcion_curvas)
                else:
                    self.Animacion = Graficacion2D_NoTemporal(self.MostrarSolucion, self.introducirProyeccion2D, fargs=[int(len(self.DatosGrafica[0])/10), *self.DatosGrafica[0:-2], self.Coordenadas, self.Valores, self.MostrarSolucion.axes, self.Cota, self.Colormap, self.GuardarAnimacion], maximo = int(len(self.DatosGrafica[0])/10)+1, interval = 1000/self.DatosGrafica[-1], curvas_nivel = self.curvas, funcion_curvas = self.funcion_curvas)
            elif len(self.Dominio) == 3:
                # Para problemas con tres dimensiones espaciales.
                if coordenada_especifica == None:
                    if self.Coordenadas == "Cartesianas":
                        self.DatosGrafica = self.crearProyeccion3D_cartesianas("x")
                        coordenada_especifica = "x"
                    elif self.Coordenadas == "Cilíndricas / Polares":
                        self.DatosGrafica = self.crearProyeccion3D_cilindricas("r")
                        coordenada_especifica = "r"
                    elif self.Coordenadas == "Esféricas":
                        self.DatosGrafica = self.crearProyeccion3D_esfericas("r")
                        coordenada_especifica = "r"

                    self.CoordenadaFija_1.setChecked(True)
                    self.Valores = self.MatrizResultados.T.swapaxes(1, 2)
                    limites = self.dominio[0:2]
                else:
                    if self.Coordenadas == "Cartesianas":
                        self.DatosGrafica = self.crearProyeccion3D_cartesianas(self.MostrarSolucion, coordenada_especifica)
                    elif self.Coordenadas == "Cilíndricas / Polares":
                        self.DatosGrafica = self.crearProyeccion3D_cilindricas(self.MostrarSolucion, coordenada_especifica)
                    elif self.Coordenadas == "Esféricas":
                        self.DatosGrafica = self.crearProyeccion3D_esfericas(self.MostrarSolucion, coordenada_especifica)
                        self.Valores = self.MatrizResultados.T.swapaxes(1, 2)
                    if coordenada_especifica == "x" or coordenada_especifica == "r":
                        limites = self.dominio[0:2]
                    elif coordenada_especifica == "y" or (coordenada_especifica == "phi" and self.Coordenadas == "Cilíndricas / Polares") or (coordenada_especifica == "theta" and self.Coordenadas == "Esféricas"):
                        self.Valores = self.MatrizResultados.T.swapaxes(0, 1).swapaxes(1, 2)
                        limites = self.dominio[2:4]
                    elif coordenada_especifica == "z" or (coordenada_especifica == "phi" and self.Coordenadas == "Esféricas"):
                        self.Valores = self.MatrizResultados
                        limites = self.dominio[4:]
                    
                self.CoordenadaFija.setText("{}".format(limites[0]))
                # Activación de la herramienta de curvas de nivel.
                self.CurvasNivelAuto.setEnabled(True)
                self.CurvasNivelEspecificas.setEnabled(True)
                self.label_11.setEnabled(True)
                self.label_11.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(246, 247, 247)")
                self.label_12.setEnabled(True)
                self.label_12.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(246, 247, 247)")
                self.CurvasNivelEspecificasEntrada.setEnabled(True)

                if (coordenada_especifica == "r") and (self.Coordenadas == "Esféricas"):
                    # Para gráfica en coordenadas esféricas y donde la coordenada fija es el radio.
                    self.Animacion = ReproductorGeneral(self.MostrarSolucion, self.actualizarProyeccion3D_especial, fargs=[int(len(self.DatosGrafica[1])/10), *self.DatosGrafica[0:2], *self.DatosGrafica[3:-1], self.Valores, limites, self.MostrarSolucion.figura, self.Cota, self.Colormap, self.GuardarAnimacion], maximo = int(len(self.DatosGrafica[1])/10+self.DatosGrafica[-2]), interval = 1000/self.DatosGrafica[-1], curvas_nivel = self.curvas, funcion_curvas = self.funcion_curvas)
                else:
                    self.Animacion = ReproductorGeneral(self.MostrarSolucion, self.actualizarProyeccion3D, fargs=[int(len(self.DatosGrafica[0])/10), *self.DatosGrafica[0:2], *self.DatosGrafica[3:-1], self.Coordenadas, self.Valores, self.MostrarSolucion.axes, coordenada_especifica, limites, self.Cota, self.Colormap, self.GuardarAnimacion], maximo = int(len(self.DatosGrafica[0])/10+self.DatosGrafica[-2]), interval = 1000/self.DatosGrafica[-1], curvas_nivel = self.curvas, funcion_curvas = self.funcion_curvas)
        else:   
            # Cuando no se requiere la proyección.
            if (len(self.Dominio) == 2) and (len(self.Dominio[-1]) == 1):
                # Para problemas de una dimensión espacial y con dependencia temporal.
                # Este código (las siguientes 5 líneas) está basado en ImportanceOfBeingErnest. (17 de diciembre de 2017). Respuesta a la pregunta "Plot curve with blending line colors with matplotlib/pyplot". stackoverflow. https://stackoverflow.com/a/47856091
                # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 3.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/3.0/
                self.Segmentos = [None for indice_nulo in self.t_grid]
                for indice in range(len(self.t_grid)):
                    puntos = np.array([self.Dominios[0], self.MatrizResultados[indice]]).T.reshape(-1, 1, 2)
                    self.Segmentos[indice] = np.concatenate([puntos[:-1], puntos[1:]], axis=1)
                self.DatosGrafica = self.crearGrafica1D(self.MostrarSolucion)
                self.Animacion =ReproductorGeneral(self.MostrarSolucion,self.actualizarAnimacion1D,fargs=[int(len(self.DatosGrafica[0])/10), *self.DatosGrafica, self.Segmentos, self.MatrizResultados, self.MostrarSolucion.axes, None, None, self.Cota, self.Colormap, self.GuardarAnimacion], maximo = int(len(self.DatosGrafica[0])/10+self.DatosGrafica[-2]*self.DatosGrafica[-1]+1), interval = 1000/self.DatosGrafica[-1], curvas_nivel = self.curvas, funcion_curvas = self.funcion_curvas)
            elif (len(self.Dominio) == 2) or (len(self.Dominio[-1]) == 1):
                # Para problemas de dos dimensiones espaciales con o sin dependencia temporal.
                if self.Coordenadas == "Cartesianas":
                    self.DatosGrafica = self.crearGrafica2D_cartesianas(self.MostrarSolucion)
                elif self.Coordenadas == "Cilíndricas / Polares":
                    self.DatosGrafica = self.crearGrafica2D_polares(self.MostrarSolucion)

                # Determinación del número de puntos en las particiones de los dominios.
                self.rcount = self.MatrizResultados.shape[0]
                self.ccount = self.MatrizResultados.shape[1]

                self.Valores = self.MatrizResultados

                if self.dependencia_tiempo:
                    self.Animacion = ReproductorGeneral(self.MostrarSolucion, self.actualizarAnimacion2D, fargs=[int(len(self.DatosGrafica[0].T)/10), *self.DatosGrafica, self.Coordenadas, self.Valores, self.MostrarSolucion.axes, self.rcount, self.ccount, self.Cota, self.Colormap, self.GuardarAnimacion], maximo = int(len(self.DatosGrafica[0].T)/10+self.DatosGrafica[-2]*self.DatosGrafica[-1]+1), interval = 1000/self.DatosGrafica[-1], curvas_nivel = self.curvas, funcion_curvas = self.funcion_curvas)
                else:
                    self.Animacion = Graficacion2D_NoTemporal(self.MostrarSolucion, self.introducirGrafica2D, fargs=[int(len(self.DatosGrafica[0].T)/10), *self.DatosGrafica, self.Coordenadas, self.MatrizResultados, self.MostrarSolucion.axes, self.rcount, self.ccount, self.Cota, self.Colormap, self.GuardarAnimacion], maximo = int(len(self.DatosGrafica[0].T)/10+1), interval = 1000/self.DatosGrafica[-1], curvas_nivel = self.curvas, funcion_curvas = self.funcion_curvas)
            elif len(self.Dominio) == 3:
                # Para problemas con tres dimensiones espaciales.
                if coordenada_especifica == None:
                    if self.Coordenadas == "Cartesianas":
                        self.DatosGrafica = self.crearGrafica3D_cartesianas(self.MostrarSolucion, "x")
                        longitud2 = int(len(self.Dominios[1])/10)
                        coordenada_especifica = "x"
                    elif self.Coordenadas == "Cilíndricas / Polares":
                        self.DatosGrafica = self.crearGrafica3D_cilindricas(self.MostrarSolucion, "r")
                        longitud2 = int(len(self.Dominios[2])/10)
                        coordenada_especifica = "r"
                    elif self.Coordenadas == "Esféricas":
                        self.DatosGrafica = self.crearGrafica3D_esfericas(self.MostrarSolucion, "r")
                        longitud2 = int(len(self.Dominios[1])/10)
                        coordenada_especifica = "r"

                    self.Valores = self.MatrizResultados.T.swapaxes(1, 2)
                    limites = self.dominio[0:2]
                    self.CoordenadaFija_1.setChecked(True)
                else:
                    if coordenada_especifica == "x" or coordenada_especifica == "r":
                        self.Valores = self.MatrizResultados.T.swapaxes(1, 2)
                        if self.Coordenadas == "Cartesianas":
                            self.DatosGrafica = self.crearGrafica3D_cartesianas(self.MostrarSolucion, "x")
                            longitud2 = int(len(self.Dominios[1])/10)
                        elif self.Coordenadas == "Cilíndricas / Polares":
                            self.DatosGrafica = self.crearGrafica3D_cilindricas(self.MostrarSolucion, "r")
                            longitud2 = int(len(self.Dominios[2])/10)
                        elif self.Coordenadas == "Esféricas":
                            self.DatosGrafica = self.crearGrafica3D_esfericas(self.MostrarSolucion, "r")
                            longitud2 = int(len(self.Dominios[1])/10)
                        limites = self.dominio[0:2]
                        
                    elif coordenada_especifica == "y" or (coordenada_especifica == "phi" and self.Coordenadas == "Cilíndricas / Polares") or (coordenada_especifica == "theta" and self.Coordenadas == "Esféricas"):
                        self.Valores = self.MatrizResultados.T.swapaxes(0, 1).swapaxes(1, 2)
                        if self.Coordenadas == "Cartesianas":
                            self.DatosGrafica = self.crearGrafica3D_cartesianas(self.MostrarSolucion, "y")
                        elif self.Coordenadas == "Cilíndricas / Polares":
                            self.DatosGrafica = self.crearGrafica3D_cilindricas(self.MostrarSolucion, "phi")
                        elif self.Coordenadas == "Esféricas":
                            self.DatosGrafica = self.crearGrafica3D_esfericas(self.MostrarSolucion, "theta")
                        longitud2 = int(len(self.Dominios[0])/10)
                        limites = self.dominio[2:4]

                    elif coordenada_especifica == "z" or (coordenada_especifica == "phi" and self.Coordenadas == "Esféricas"):
                        self.Valores = self.MatrizResultados
                        if self.Coordenadas == "Cartesianas":
                            self.DatosGrafica = self.crearGrafica3D_cartesianas(self.MostrarSolucion, "z")
                        elif self.Coordenadas == "Cilíndricas / Polares":
                            self.DatosGrafica = self.crearGrafica3D_cilindricas(self.MostrarSolucion, "z")
                        elif self.Coordenadas == "Esféricas":
                            self.DatosGrafica = self.crearGrafica3D_esfericas(self.MostrarSolucion, "phi")
                        longitud2 = int(len(self.Dominios[0])/10)
                        limites = self.dominio[4:]
                
                # Desactivación de la herramienta de curvas de nivel.
                self.CurvasNivelAuto.setEnabled(False)
                self.label_11.setEnabled(False)
                self.label_11.setStyleSheet(u"color: rgba(11, 61, 98, 0.3); background-color: rgb(246, 247, 247)")
                self.label_12.setEnabled(False)
                self.label_12.setStyleSheet(u"color: rgba(11, 61, 98, 0.3); background-color: rgb(246, 247, 247)")
                self.CurvasNivelEspecificas.setEnabled(False)
                self.CurvasNivelEspecificasEntrada.setEnabled(False)

                # Determinación del número de puntos en las particiones de los dominios.
                self.rcount = self.Valores.shape[1]
                self.ccount = self.Valores.shape[2]        

                self.Animacion = ReproductorGeneral(self.MostrarSolucion, self.actualizarGrafica3D, fargs=[longitud2, *self.Dominios, self.x, self.y, self.DatosGrafica[0], self.Coordenadas, coordenada_especifica, plt.Normalize(vmin = -self.Cota, vmax = self.Cota), self.Valores, self.MostrarSolucion.axes, limites, self.rcount, self.ccount, self.Cota, self.Colormap, self.GuardarAnimacion], maximo = int(longitud2+self.DatosGrafica[0]), interval = 1000/self.DatosGrafica[-1], curvas_nivel = self.curvas, funcion_curvas = self.funcion_curvas)

        self.envioActualizacion("Mostrando Coeficientes y Valores")

        self.calcularValorSolucion()
        self.signals.finalizar_signal.emit("Gráfica Lista")

    def actualizarAnimacion1D(self, cuadro, cuadro_fijo, x, linea, tiempo_total, resolucion, segmentos, valores_matriz, lienzo, valor_nulo, valor_nulo2, valor_nulo3):
        """
        Actualiza la gráfica dentro de la animación en problemas de una dimensión espacial con dependencia temporal.
        
        Parámetros
        ----------
        cuadro: entero
            Cuadro actual de la animación.

        cuadro_fijo: entero
            Cuadro inicial del reproductor.

        x: lista flotantes
            Particion del dominio x.

        linea: conjunto de líneas de Matplotlib concatenadas
            Gráfica de la solución.

        tiempo_total: flotante
            Tiempo máximo hasta el que se calculó la solución.

        resolucion: entero
            FPS de la animación.

        segmentos: conjunto de líneas de Matplotlib
            Gráfica de la solución partida a trozos.

        valores_matriz: arreglo bidimensional de flotantes
            Valores de la solución.
        
        lienzo: Matplotlib.axes
            Lienzo de la solución.

        *valor_nulo, valor_nulo2, valor_nulo3*: no especificados
            Parámetros para estandarizar las funciones de animación para la reproducción y guardado de las animaciones.
        """

        self.valorespecial = False

        if cuadro < -1:
            # Inicialización de la gráfica.
            linea.set_segments([])
        elif 0 <= cuadro <= cuadro_fijo:
            # Creación de la gráfica para el tiempo t=0.
            linea.set_segments(segmentos[0][:cuadro*10+int(len(x)%10)])
        elif cuadro_fijo+1 <= cuadro <= cuadro_fijo+tiempo_total*resolucion+1:
            # Actualización de la gráfica para tiempos posteriores.
            tiempo = cuadro-cuadro_fijo-1
            linea.set_segments(segmentos[tiempo])
            linea.set_array(valores_matriz[tiempo])
            lienzo.set_title(' Tiempo \n{:02d}:{:02d}.{:02d}'.format(int(tiempo*0.04//60), int(tiempo*0.04%60), int((tiempo*0.04*100)%100)), pad = 10)
        return linea
    
    def introducirProyeccion1D(self, cuadro, x, t, tiempo_total, resolucion, valores_matriz, lienzo, cota):
        """
        Crea el mapa de calor para problemas con una dimensión espacial y dependencia temporal.
        
        Parámetros
        ----------
        cuadro: entero
            Cuadro actual de la animación.

        cuadro_fijo: entero
            Cuadro inicial del reproductor.

        x: lista flotantes
            Particion del dominio x.

        tiempo_total: flotante
            Tiempo máximo hasta el que se calculó la solución.

        resolucion: entero
            FPS de la animación.

        valores_matriz: arreglo bidimensional de flotantes
            Valores de la solución.

        lienzo: Matplotlib.axes
            Lienzo de la solución.

        cota: flotante
            Cota de los valores de la solución.
        """

        self.valorespecial = False

        if cuadro < 0:
            # Inicialización de la gráfica.
            tiempo = 0
            coordenada1, coordenada2 = np.meshgrid([0], [0])
            Z = coordenada1**2+coordenada2**2
            lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
            lienzo.set_title(' Tiempo \n{:02d}:{:02d}.{:02d}'.format(int(tiempo*0.04//60), int(tiempo*0.04%60), int((tiempo*0.04*100)%100)), pad = 10)
        elif 0 <= cuadro <= tiempo_total*resolucion:
            # Creación de la gráfica.
            tiempo = cuadro
            lienzo.proyeccion.remove()
            lienzo.proyeccion = lienzo.pcolormesh(t[:cuadro+1], x, valores_matriz[:cuadro+1].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
            lienzo.set_title(' Tiempo \n{:02d}:{:02d}.{:02d}'.format(int(tiempo*0.04//60), int(tiempo*0.04%60), int((tiempo*0.04*100)%100)), pad = 10)
        return lienzo
    
    def actualizarAnimacion2D(self, cuadro, cuadro_fijo, coordenada1, coordenada2, tiempo_total, resolucion, coordenadas, valores_matriz, lienzo, numero_columnas, numero_filas, cota):
        """
        Actualiza la gráfica dentro de la animación en problemas con dos dimensiones espaciales.
        
        Parámetros
        ----------
        cuadro: entero
            Cuadro actual de la animación.

        cuadro_fijo: entero
            Cuadro inicial del reproductor.

        coordenada1: lista flotantes
            Particion del dominio de la primera coordenada espacial.

        coordenada2: lista flotantes
            Particion del dominio de la segunda coordenada espacial. 

        tiempo_total: flotante
            Tiempo máximo hasta el que se calculó la solución.

        resolucion: entero
            FPS de la animación.   

        valores_matriz: arreglo bidimensional de flotantes
            Valores de la solución.

        lienzo: Matplotlib.axes
            Lienzo de la solución.

        numero_columnas: entero
            Número de puntos en la partición de la segunda coordenada.

        numero_filas: entero
            Número de puntos en la partición de la primera coordenada.
        
        cota: flotante
            Cota de valores de la solución.

        *coordenadas*: no especificado
            Parámetro para estandarizar las funciones de animación para el guardado de las animaciones.
        """

        self.valorespecial = False

        if cuadro == -1:
            # Inicialización de la gráfica.
            coordenada1, coordenada2 = np.meshgrid([0], [0])
            Z = coordenada1**2+coordenada2**2
            lienzo.superficie = lienzo.plot_surface(coordenada1, coordenada2, Z, cmap = self.Colormap, vmin=-cota, vmax=cota)
        elif 0 <= cuadro <= cuadro_fijo:
            # Creación de la gráfica para el tiempo t = 0.
            lienzo.superficie.remove()
            lienzo.superficie = lienzo.plot_surface(coordenada1.T[:cuadro*10+int(len(coordenada1.T)%10)], coordenada2.T[:cuadro*10+int(len(coordenada1.T)%10)], valores_matriz[0].T[:cuadro*10+int(len(coordenada1.T)%10)], cmap = self.Colormap, vmin=-cota, vmax=cota, ccount = numero_columnas, rcount = numero_filas)
        elif cuadro_fijo+1 <= cuadro <= cuadro_fijo+tiempo_total*resolucion+1:
            # Cración de la gráfica para tiempos posteriores.
            tiempo = cuadro-cuadro_fijo-1
            lienzo.superficie.remove()
            lienzo.superficie = lienzo.plot_surface(coordenada1, coordenada2, valores_matriz[tiempo], cmap = self.Colormap, vmin=-cota, vmax=cota, ccount = numero_columnas, rcount = numero_filas)
            lienzo.set_title(' Tiempo \n{:02d}:{:02d}.{:02d}'.format(int(tiempo*0.04//60), int(tiempo*0.04%60), int((tiempo*0.04*100)%100)), pad = -10)
        return lienzo
        
    def introducirGrafica2D(self, cuadro, cuadro_fijo, coordenada1, coordenada2, tiempo_total, resolucion, coordenadas, valores_matriz, lienzo, numero_columnas, numero_filas, cota):
        """
        Crea la gráfica en problemas de dos dimensiones espaciales sin dependencia temporal.
        
        Parámetros
        ----------
        cuadro: entero
            Cuadro actual de la animación.

        cuadro_fijo: entero
            Cuadro inicial del reproductor.

        coordenada1: lista flotantes
            Particion del dominio de la primera coordenada espacial.

        coordenada2: lista flotantes
            Particion del dominio de la segunda coordenada espacial.    
        
        coordenadas: string
            Sistema de coordenadas de la gráfica.

        valores_matriz: arreglo bidimensional de flotantes
            Valores de la solución.

        lienzo: Matplotlib.axes
            Lienzo de la solución.

        numero_columnas: entero
            Número de puntos en la partición de la segunda coordenada.

        numero_filas: entero
            Número de puntos en la partición de la primera coordenada.
        
        cota: flotante
            Cota de valores de la solución.
        """

        self.valorespecial = False

        if coordenadas == "Cartesianas":
            if cuadro == 0:
                # Inicialización de gráfica.
                lienzo.superficie = lienzo.plot_surface(coordenada1.T[:cuadro*10+int(len(coordenada1.T)%10)], coordenada2.T[:cuadro*10+int(len(coordenada1.T)%10)], valores_matriz.T[:cuadro*10+int(len(coordenada1.T)%10)], cmap = self.Colormap, vmin=-cota, vmax=cota, ccount = numero_columnas, rcount = numero_filas)
            elif 1 <= cuadro <= cuadro_fijo:
                # Creación de la gráfica.
                lienzo.superficie.remove()
                lienzo.superficie = lienzo.plot_surface(coordenada1.T[:cuadro*10+int(len(coordenada1.T)%10)], coordenada2.T[:cuadro*10+int(len(coordenada1.T)%10)], valores_matriz.T[:cuadro*10+int(len(coordenada1.T)%10)], cmap = self.Colormap, vmin=-cota, vmax=cota, ccount = numero_columnas, rcount = numero_filas)
        elif coordenadas == "Cilíndricas / Polares":
            if cuadro == 0:
                # Inicialización de gráfica.
                lienzo.superficie = lienzo.plot_surface(coordenada1.T[:cuadro*10+int(len(coordenada1.T)%10)], coordenada2.T[:cuadro*10+int(len(coordenada1.T)%10)], valores_matriz.T[:cuadro*10+int(len(coordenada1.T)%10)], cmap = self.Colormap, vmin=-cota, vmax=cota, ccount = numero_columnas, rcount = numero_filas)
            elif 1 <= cuadro <= cuadro_fijo:
                # Creación de la gráfica para el tiempo.
                lienzo.superficie.remove()
                lienzo.superficie = lienzo.plot_surface(coordenada1.T[:cuadro*10+int(len(coordenada1.T)%10)], coordenada2.T[:cuadro*10+int(len(coordenada1.T)%10)], valores_matriz.T[:cuadro*10+int(len(coordenada1.T)%10)], cmap = self.Colormap, vmin=-cota, vmax=cota, ccount = numero_columnas, rcount = numero_filas)
        return lienzo
        
    def actualizarProyeccion2D(self, cuadro, cuadro_fijo, coordenada1, coordenada2, tiempo_total, resolucion, coordenadas, valores_matriz, lienzo, cota):
        """
        Actualiza la proyección para problemas con dos dimensiones espaciales y dependencia temporal.
        
        Parámetros
        ----------
        cuadro: entero
            Cuadro actual de la animación.

        cuadro_fijo: entero
            Cuadro inicial del reproductor.

        coordenada1: lista flotantes
            Particion del dominio de la primera coordenada.
        
        coordenada2: lista flotantes
            Particion del dominio de la segunda coordenada.

        tiempo_total: flotante
            Tiempo máximo hasta el que se calculó la solución.

        resolucion: entero
            FPS de la animación.

        coordenadas: string
            Sistema de coordenadas.

        valores_matriz: arreglo bidimensional de flotantes
            Valores de la solución.

        lienzo: Matplotlib.axes
            Lienzo de la solución.

        cota: flotante
            Cota de los valores de la solución.
        """

        self.valorespecial = False

        if coordenadas == "Cartesianas":
            if cuadro == -1:
                # Inicialización de la gráfica.
                coordenada1, coordenada2 = np.meshgrid([0], [0])
                Z = coordenada1**2+coordenada2**2
                lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
            elif 0 <= cuadro <= cuadro_fijo:
                # Creación de la gráfica para el tiempo t = 0.
                lienzo.proyeccion.remove()
                lienzo.proyeccion = lienzo.pcolormesh(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada2, valores_matriz[0].T[:cuadro*10+int(len(coordenada1)%10)].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
            elif cuadro_fijo < cuadro <= cuadro_fijo+ tiempo_total*resolucion+1:
                # Creación de la gráfica para tiempos posteriores.
                tiempo = cuadro-cuadro_fijo-1
                lienzo.proyeccion.remove()
                lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2, valores_matriz[tiempo], cmap=self.Colormap, vmin=-cota, vmax=cota)
                lienzo.set_title(' Tiempo \n{:02d}:{:02d}.{:02d}'.format(int(tiempo*0.04//60), int(tiempo*0.04%60), int((tiempo*0.04*100)%100)), pad = -10)
        elif coordenadas == "Cilíndricas / Polares":
            if cuadro == -1:
                # Inicialización de la gráfica.
                coordenada1, coordenada2 = np.meshgrid([0], [0, 1])
                Z = 0*(coordenada1**2+coordenada2**2)
                lienzo.proyeccion = lienzo.pcolormesh(coordenada2, coordenada1, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
            elif 0 <= cuadro <= cuadro_fijo:
                # Creación de la gráfica para el tiempo t = 0.
                lienzo.proyeccion.remove()
                if (cuadro == 0) and (int(len(coordenada1)%10) == 0):
                    # Cuando el número de puntos en la partición del dominio de la primera coordenada es múltiplo de 10 y se quiere inicializar la gráfica del tiempo t = 0 se gráfican valores nulos para evitar un error.
                    coordenada1, coordenada2 = np.meshgrid([0], [0, 1])
                    Z = 0*(coordenada1**2+coordenada2**2)
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada2, coordenada1, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
                else:
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada2, valores_matriz[0][:cuadro*10+int(len(coordenada1)%10)].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
            elif cuadro_fijo < cuadro <= cuadro_fijo+ tiempo_total*resolucion+1:
                # Creación de la gráfica para tiempos posteriores.
                tiempo = cuadro-cuadro_fijo-1
                lienzo.proyeccion.remove()
                lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2, valores_matriz[tiempo].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
                lienzo.set_title(' Tiempo \n{:02d}:{:02d}.{:02d}'.format(int(tiempo*0.04//60), int(tiempo*0.04%60), int((tiempo*0.04*100)%100)), pad = -10)
        return lienzo
    
    def introducirProyeccion2D(self, cuadro, cuadro_fijo, coordenada1, coordenada2, coordenadas, valores_matriz, lienzo, cota):
        """
        Crea la proyeccion en problemas de dos dimensiones espaciales sin dependencia temporal.
        
        Parámetros
        ----------
        cuadro: entero
            Cuadro actual de la animación.

        cuadro_fijo: entero
            Cuadro inicial del reproductor.

        coordenada1: lista flotantes
            Particion del dominio de la primera coordenada espacial.

        coordenada2: lista flotantes
            Particion del dominio de la segunda coordenada espacial.    
        
        coordenadas: string
            Sistema de coordenadas de la gráfica.

        valores_matriz: arreglo bidimensional de flotantes
            Valores de la solución.

        lienzo: Matplotlib.axes
            Lienzo de la solución.
        
        cota: flotante
            Cota de valores de la solución.
        """

        self.valorespecial = False

        if coordenadas == "Cartesianas":
            if cuadro == -1:
                # Inicialización de la gráfica.
                coordenada1, coordenada2 = np.meshgrid([0], [0])
                Z = coordenada1**2+coordenada2**2
                lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
            elif 0 <= cuadro <= cuadro_fijo:
                # Creación de la gráfica.
                lienzo.proyeccion.remove()
                lienzo.proyeccion = lienzo.pcolormesh(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada2, valores_matriz.T[:cuadro*10+int(len(coordenada1)%10)].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
        elif coordenadas == "Cilíndricas / Polares":
            if cuadro == -1:
                # Inicialización de la gráfica.
                coordenada1, coordenada2 = np.meshgrid([0], [0, 1])
                Z = 0*(coordenada1**2+coordenada2**2)
                lienzo.proyeccion = lienzo.pcolormesh(coordenada2, coordenada1, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
            elif 0 <= cuadro <= cuadro_fijo:
                # Creación de la gráfica.
                lienzo.proyeccion.remove()
                if (cuadro == 0) and (int(len(coordenada1)%10) == 0):
                    # Cuando el número de puntos en la partición del dominio de la primera coordenada es múltiplo de 10 y se quiere inicializar la gráfica del tiempo t = 0 se gráfican valores nulos para evitar un error.
                    coordenada1, coordenada2 = np.meshgrid([0], [0, 1])
                    Z = 0*(coordenada1**2+coordenada2**2)
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada2, coordenada1, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
                else: 
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada2, valores_matriz[:cuadro*10+int(len(coordenada1)%10)].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
        return lienzo.proyeccion
    
    def actualizarGrafica3D(self, cuadro, cuadro_fijo, coordenada1, coordenada2, coordenada3, grid1, grid2, longitud, coordenadas, coordenada_fija, norma, valores_matriz, lienzo, limites, numero_columnas, numero_filas, cota):
        """
        Actualiza la gráfica en problemas de tres dimensiones espaciales.
        
        Parámetros
        ----------
        cuadro: entero
            Cuadro actual de la animación.

        cuadro_fijo: entero
            Cuadro inicial del reproductor.

        coordenada1: lista flotantes
            Particion del dominio de la primera coordenada espacial.

        coordenada2: lista flotantes
            Particion del dominio de la segunda coordenada espacial.   

        coordenada3: lista flotantes
            Particion del dominio de la tercera coordenada espacial.  

        grid1: Numpy meshgrid
            Meshgrid de la primera coordenada base.
    
        grid2: Numpy meshgrid
            Meshgrid de la segunda coordenada base.

        longitud: entero
            Longitud de la partición de la coordenada fija.
        
        coordenadas: string
            Sistema de coordenadas de la gráfica.

        coordenada_fija: string
            Coordenada fija de la gráfica.

        valores_matriz: arreglo bidimensional de flotantes
            Valores de la solución.

        lienzo: Matplotlib.axes
            Lienzo de la solución.

        limites: lista de dos flotantes
            Extremos del dominio de la coordenada fija.

        numero_columnas: entero
            Número de puntos en la partición de la segunda coordenada.

        numero_filas: entero
            Número de puntos en la partición de la primera coordenada.
        
        cota: flotante
            Cota de valores de la solución.
        """

        # La graficación de cortes en x o en y en el sistema de coordenadas cartesiano se basa en Joe. (14 de octubre de 2019). Respuesta a la pregunta "How to plot a plane that is parallel to both of x-axis and z-axis with python?". stackoverflow. https://stackoverflow.com/a/58371196
        # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 4.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/4.0/
        
        # La graficación de cortes en coordenadas cilíndricas y/o esféricas se basa en unutbu. (23 de abril de 2016). Respuesta a la pregunta "Spherical coordinates plot". stackoverflow. https://stackoverflow.com/a/36816821
        # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 3.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/3.0/

        self.valorespecial = False

        if coordenadas == "Cartesianas":
            if coordenada_fija == "x":
                if cuadro == -1:
                    # Inicialización de la gráfica.
                    coordenada1, coordenada2 = np.meshgrid([0], [0])
                    coordenada3 = coordenada1**2+coordenada2**2
                    lienzo.superficie = lienzo.plot_surface(coordenada1, coordenada2, coordenada3, cmap = self.Colormap, vmin=-cota, vmax=cota)
                elif 0 <= cuadro <= cuadro_fijo:
                    # Creación de la gráfica para el primer valor de la coordenada fija.
                    lienzo.superficie.remove()
                    y, z = np.meshgrid(coordenada2[:cuadro*10+int(len(coordenada2)%10)], coordenada3)

                    # La coloración de los cortes se basa en Elrond. (21 de marzo de 2017). Colorbar for matplotlib plot_surface using facecolors. stackoverflow. https://stackoverflow.com/q/42924993
                    # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 3.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/3.0/
                    lienzo.superficie = lienzo.plot_surface(coordenada1[0], y, z, facecolors = self.Colormap(norma(valores_matriz[0].T[:cuadro*10+int(len(coordenada2)%10)].T)), shade=False, ccount = numero_columnas, rcount = numero_filas)

                elif cuadro_fijo+1 <= cuadro <= cuadro_fijo+longitud:
                    # Creación de la gráfica para los demás valores.
                    indice = cuadro-cuadro_fijo-1
                    lienzo.superficie.remove()
                    lienzo.superficie = lienzo.plot_surface(coordenada1[indice], grid1, grid2, facecolors = self.Colormap(norma(valores_matriz[indice])), shade=False, ccount = numero_columnas, rcount = numero_filas)
                    lienzo.set_title(r'$x = %(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = -10)
            elif coordenada_fija == "y":
                if cuadro == -1:
                    # Inicialización de la gráfica.
                    coordenada1, coordenada2 = np.meshgrid([0], [0])
                    coordenada3 = coordenada1**2+coordenada2**2
                    lienzo.superficie = lienzo.plot_surface(coordenada1, coordenada2, coordenada3, cmap = self.Colormap, vmin=-cota, vmax=cota)
                elif 0 <= cuadro <= cuadro_fijo:
                    # Creación de la gráfica para el primer valor de la coordenada fija.
                    lienzo.superficie.remove()
                    x, z = np.meshgrid(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada3)
                    lienzo.superficie = lienzo.plot_surface(x, coordenada2[0], z, facecolors = self.Colormap(norma(valores_matriz[0].T[:cuadro*10+int(len(coordenada1)%10)].T)), shade=False, ccount = numero_columnas, rcount = numero_filas)
                elif cuadro_fijo+1 <= cuadro <= cuadro_fijo+longitud:
                    # Creación de la gráfica para los demás valores.
                    indice = cuadro-cuadro_fijo-1
                    lienzo.superficie.remove()
                    lienzo.superficie = lienzo.plot_surface(grid1, coordenada2[indice], grid2, facecolors = self.Colormap(norma(valores_matriz[indice])), shade=False, ccount = numero_columnas, rcount = numero_filas)
                    lienzo.set_title(r'$y = %(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = -10)
            elif coordenada_fija == "z":
                if cuadro == -1:
                    # Inicialiación de la gráfica.
                    coordenada1, coordenada2 = np.meshgrid([0], [0])
                    coordenada3 = coordenada1**2+coordenada2**2
                    lienzo.superficie = lienzo.plot_surface(coordenada1, coordenada2, coordenada3, cmap = self.Colormap, vmin=-cota, vmax=cota)            
                elif 0 <= cuadro <= cuadro_fijo:
                    # Creación de la gráfica para el primer valor de la coordenada fija.
                    lienzo.superficie.remove()
                    x, y = np.meshgrid(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada2)
                    lienzo.superficie = lienzo.plot_surface(x, y, coordenada3[0]*(1+(x**2+y**2)*0), facecolors = self.Colormap(norma(valores_matriz[0].T[:cuadro*10+int(len(coordenada1)%10)].T)), shade=False, ccount = numero_columnas, rcount = numero_filas)
                elif cuadro_fijo+1 <= cuadro <= cuadro_fijo+longitud:
                    # Creación de la gráfica para los demás valores.
                    indice = cuadro-cuadro_fijo-1
                    lienzo.superficie.remove()
                    lienzo.superficie = lienzo.plot_surface(grid1, grid2, coordenada3[indice]*(1+(grid1**2+grid2**2)*0), facecolors = self.Colormap(norma(valores_matriz[indice])), shade=False, ccount = numero_columnas, rcount = numero_filas)
                    lienzo.set_title(r'$z = %(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = -10)
        elif coordenadas == "Cilíndricas / Polares":
            if coordenada_fija == "r":
                if cuadro == -1:
                    # Inicialización de la gráfica.
                    coordenada1, coordenada2 = np.meshgrid([0], [0])
                    coordenada3 = coordenada1**2+coordenada2**2
                    lienzo.superficie = lienzo.plot_surface(coordenada1, coordenada2, coordenada3, cmap = self.Colormap, vmin=-cota, vmax=cota)
                elif 0 <= cuadro <= cuadro_fijo:
                    # Creación de la gráfica para el primer valor de la coordenada fija.
                    lienzo.superficie.remove()
                    phi, z = np.meshgrid(coordenada2, coordenada3[:cuadro*10+int(len(coordenada3)%10)])
                    x, y = coordenada1[0]*np.cos(phi), coordenada1[0]*np.sin(phi)
                    lienzo.superficie = lienzo.plot_surface(x, y, z, facecolors = self.Colormap(norma(valores_matriz[0][:cuadro*10+int(len(coordenada3)%10)])), shade=False, ccount = numero_columnas, rcount = numero_filas)
                elif cuadro_fijo+1 <= cuadro <= cuadro_fijo+longitud:
                    # Creación de la gráfica para los demás valores.
                    indice = cuadro-cuadro_fijo-1
                    lienzo.superficie.remove()
                    x, y = coordenada1[indice]*np.cos(grid1), coordenada1[indice]*np.sin(grid1)
                    lienzo.superficie = lienzo.plot_surface(x, y, grid2, facecolors = self.Colormap(norma(valores_matriz[indice])), shade=False, ccount = numero_columnas, rcount = numero_filas)
                    lienzo.set_title(r'$r = %(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = -10)
            elif coordenada_fija == "phi":
                if cuadro == -1:
                    # Inicialización de la gráfica.
                    coordenada1, coordenada2 = np.meshgrid([0], [0])
                    coordenada3 = coordenada1**2+coordenada2**2
                    lienzo.superficie = lienzo.plot_surface(coordenada1, coordenada2, coordenada3, cmap = self.Colormap, vmin=-cota, vmax=cota)
                elif 0 <= cuadro <= cuadro_fijo:
                    # Creación de la gráfica para el primer valor de la coordenada fija.
                    lienzo.superficie.remove()
                    r, z = np.meshgrid(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada3)
                    x, y = r*np.cos(coordenada2[0]), r*np.sin(coordenada2[0])
                    lienzo.superficie = lienzo.plot_surface(x, y, z, facecolors = self.Colormap(norma(valores_matriz[0].T[:cuadro*10+int(len(coordenada1)%10)].T)), shade=False, ccount = numero_columnas, rcount = numero_filas)
                elif cuadro_fijo+1 <= cuadro <= cuadro_fijo+longitud:
                    # Creación de la gráfica para los demás valores.
                    indice = cuadro-cuadro_fijo-1
                    lienzo.superficie.remove()
                    x, y = grid1*np.cos(coordenada2[indice]), grid1*np.sin(coordenada2[indice])
                    lienzo.superficie = lienzo.plot_surface(x, y, grid2, facecolors = self.Colormap(norma(valores_matriz[indice])), shade=False, ccount = numero_columnas, rcount = numero_filas)
                    lienzo.set_title(r'$\phi = %(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = -10)
            elif coordenada_fija == "z":
                if cuadro == -1:
                    # Inicialización de la gráfica.
                    coordenada1, coordenada2 = np.meshgrid([0], [0])
                    coordenada3 = coordenada1**2+coordenada2**2
                    lienzo.superficie = lienzo.plot_surface(coordenada1, coordenada2, coordenada3, cmap = self.Colormap, vmin=-cota, vmax=cota) 
                elif 0 <= cuadro <= cuadro_fijo:
                    # Creación de la gráfica para el primer valor de la coordenada fija.
                    lienzo.superficie.remove()
                    r, phi = np.meshgrid(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada2)
                    x, y = r*np.cos(phi), r*np.sin(phi)
                    lienzo.superficie = lienzo.plot_surface(x, y, coordenada3[0]*(1+(x**2+y**2)*0), facecolors = self.Colormap(norma(valores_matriz[0].T[:cuadro*10+int(len(coordenada1)%10)].T)), shade=False, ccount = numero_columnas, rcount = numero_filas)
                elif cuadro_fijo+1 <= cuadro <= cuadro_fijo+longitud:
                    # Creación de la gráfica para los demás valores.
                    indice = cuadro-cuadro_fijo-1
                    lienzo.superficie.remove()
                    lienzo.superficie = lienzo.plot_surface(grid1, grid2, coordenada3[indice]*(1+(grid1**2+grid2**2)*0), facecolors = self.Colormap(norma(valores_matriz[indice])), shade=False, ccount = numero_columnas, rcount = numero_filas)
                    lienzo.set_title(r'$z = %(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = -10)
        elif coordenadas == "Esféricas":
            if coordenada_fija == "r":
                if cuadro == -1:
                    # Inicialización de la gráfica.
                    coordenada1, coordenada2 = np.meshgrid([0], [0])
                    coordenada3 = coordenada1**2+coordenada2**2
                    lienzo.superficie = lienzo.plot_surface(coordenada1, coordenada2, coordenada3, cmap = self.Colormap, vmin=-cota, vmax=cota)
                elif 0 <= cuadro <= cuadro_fijo:
                    # Creación de la gráfica para el primer valor de la coordenada fija.
                    lienzo.superficie.remove()
                    theta, phi = np.meshgrid(coordenada2[:cuadro*10+int(len(coordenada2)%10)], coordenada3)
                    x, y = coordenada1[0]*np.cos(phi)*np.sin(theta), coordenada1[0]*np.sin(phi)*np.sin(theta)
                    z = coordenada1[0]*np.cos(theta)
                    lienzo.superficie = lienzo.plot_surface(x, y, z, facecolors = self.Colormap(norma(valores_matriz[0].T[:cuadro*10+int(len(coordenada2)%10)].T)), shade=False, ccount = numero_columnas, rcount = numero_filas)
                elif cuadro_fijo+1 <= cuadro <= cuadro_fijo+longitud:
                    # Creación de la gráfica para los demás valores.
                    indice = cuadro-cuadro_fijo-1
                    lienzo.superficie.remove()
                    x, y = coordenada1[indice]*np.cos(grid2)*np.sin(grid1), coordenada1[indice]*np.sin(grid2)*np.sin(grid1)
                    z = coordenada1[indice]*np.cos(grid1)
                    lienzo.superficie = lienzo.plot_surface(x, y, z, facecolors = self.Colormap(norma(valores_matriz[indice])), shade=False, ccount = numero_columnas, rcount = numero_filas)
                    lienzo.set_title(r'$r = %(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = -10)
            elif coordenada_fija == "theta":
                if cuadro == -1:
                    # Inicialización de la gráfica.
                    coordenada1, coordenada2 = np.meshgrid([0], [0])
                    coordenada3 = coordenada1**2+coordenada2**2
                    lienzo.superficie = lienzo.plot_surface(coordenada1, coordenada2, coordenada3, cmap = self.Colormap, vmin=-cota, vmax=cota)
                elif 0 <= cuadro <= cuadro_fijo:
                    # Creación de la gráfica para el primer valor de la coordenada fija.
                    lienzo.superficie.remove()
                    r, phi = np.meshgrid(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada3)
                    x, y = r*np.cos(phi)*np.sin(coordenada2[0]), r*np.sin(phi)*np.sin(coordenada2[0])
                    z = r*np.cos(coordenada2[0])
                    lienzo.superficie = lienzo.plot_surface(x, y, z, facecolors = self.Colormap(norma(valores_matriz[0].T[:cuadro*10+int(len(coordenada1)%10)].T)), shade=False, ccount = numero_columnas, rcount = numero_filas)
                elif cuadro_fijo+1 <= cuadro <= cuadro_fijo+longitud:
                    # Creación de la gráfica para los demás valores.
                    indice = cuadro-cuadro_fijo-1
                    lienzo.superficie.remove()
                    x, y = grid1*np.cos(grid2)*np.sin(coordenada2[indice]), grid1*np.sin(grid2)*np.sin(coordenada2[indice])
                    z = grid1*np.cos(coordenada2[indice])
                    lienzo.superficie = lienzo.plot_surface(x, y, z, facecolors = self.Colormap(norma(valores_matriz[indice])), shade=False, ccount = numero_columnas, rcount = numero_filas)
                    lienzo.set_title(r'$\phi = %(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = -10)
            elif coordenada_fija == "phi":
                if cuadro == -1:
                    # Inicialización de la gráfica.
                    coordenada1, coordenada2 = np.meshgrid([0], [0])
                    coordenada3 = coordenada1**2+coordenada2**2
                    lienzo.superficie = lienzo.plot_surface(coordenada1, coordenada2, coordenada3, cmap = self.Colormap, vmin=-cota, vmax=cota)
                elif 0 <= cuadro <= cuadro_fijo:
                    # Creación de la gráfica para el primer valor de la coordenada fija.
                    lienzo.superficie.remove()
                    r, t = np.meshgrid(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada2)
                    x, y = r*np.cos(coordenada3[0])*np.sin(t), r*np.sin(coordenada3[0])*np.sin(t)
                    z = r*np.cos(t)
                    lienzo.superficie = lienzo.plot_surface(x, y, z, facecolors = self.Colormap(norma(valores_matriz[0].T[:cuadro*10+int(len(coordenada1)%10)].T)), shade=False, ccount = numero_columnas, rcount = numero_filas)
                elif cuadro_fijo+1 <= cuadro <= cuadro_fijo+longitud:
                    # Creación de la gráfica para los demás valores.
                    indice = cuadro-cuadro_fijo-1
                    lienzo.superficie.remove()
                    x, y = grid1*np.cos(coordenada3[indice])*np.sin(grid2), grid1*np.sin(coordenada3[indice])*np.sin(grid2)
                    z = grid1*np.cos(grid2)
                    lienzo.superficie = lienzo.plot_surface(x, y, z, facecolors = self.Colormap(norma(valores_matriz[indice])), shade=False, ccount = numero_columnas, rcount = numero_filas)
                    lienzo.set_title(r'$\phi = %(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = -10)
        return lienzo
            
    def actualizarProyeccion3D(self, cuadro, cuadro_fijo, coordenada1, coordenada2, longitud, coordenadas, valores_matriz, lienzo, coordenada_fija, limites, cota):
        """
        Actualiza la proyección en problemas de tres dimensiones espaciales excepto en coordenadas esféricas y el radio como coordenada fija.
        
        Parámetros
        ----------
        cuadro: entero
            Cuadro actual de la animación.

        cuadro_fijo: entero
            Cuadro inicial del reproductor.

        coordenada1: lista flotantes
            Particion del dominio de la primera coordenada espacial.

        coordenada2: lista flotantes
            Particion del dominio de la segunda coordenada espacial.   

        longitud: entero
            Longitud de la partición de la coordenada fija.
        
        coordenadas: string
            Sistema de coordenadas de la gráfica.

        valores_matriz: arreglo bidimensional de flotantes
            Valores de la solución.

        lienzo: Matplotlib.axes
            Lienzo de la solución.

        coordenada_fija: string
            Coordenada fija de la gráfica.

        limites: lista de dos flotantes
            Extremos del dominio de la coordenada fija.
        
        cota: flotante
            Cota de valores de la solución.
        """

        self.valorespecial = False

        if coordenadas == "Cartesianas":
            if cuadro == -1:
                # Inicialización de la gráfica.
                coordenada1, coordenada2 = np.meshgrid([0], [0])
                Z = coordenada1**2+coordenada2**2
                lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
            elif 0 <= cuadro <= cuadro_fijo:
                # Creación de la gráfica para el primer valor de la coordenada fija.
                lienzo.proyeccion.remove()
                lienzo.proyeccion = lienzo.pcolormesh(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada2, valores_matriz[0].T[:cuadro*10+int(len(coordenada1)%10)].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
            elif cuadro_fijo < cuadro <= cuadro_fijo+longitud:
                # Creación de la gráfica para los demás valores.
                indice = cuadro-cuadro_fijo-1
                lienzo.proyeccion.remove()
                lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2, valores_matriz[indice], cmap=self.Colormap, vmin=-cota, vmax=cota)
                lienzo.set_title(r'$%(coordenada)s = %(valor)s $' % {"coordenada": coordenada_fija, "valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = 10)
        elif coordenadas == "Cilíndricas / Polares":
            if coordenada_fija == "r":
                if cuadro == -1:
                    # Inicialización de la gráfica.
                    coordenada1, coordenada2 = np.meshgrid([0], [0])
                    Z = coordenada1**2+coordenada2**2
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
                elif 0 <= cuadro <= cuadro_fijo:
                    # Creación de la gráfica para el primer valor de la coordenada fija.
                    lienzo.proyeccion.remove()
                    if (cuadro == 0) and (int(len(coordenada1)%10) == 0):
                        coordenada1, coordenada2 = np.meshgrid([0], [0, 1])
                        Z = 0*(coordenada1**2+coordenada2**2)
                        lienzo.proyeccion = lienzo.pcolormesh(coordenada2, coordenada1, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
                    else:
                        lienzo.proyeccion = lienzo.pcolormesh(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada2, valores_matriz[0].T[:cuadro*10+int(len(coordenada1)%10)].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
                elif cuadro_fijo < cuadro <= cuadro_fijo+longitud:
                    # Creación de la gráfica para los demás valores.
                    indice = cuadro-cuadro_fijo-1
                    lienzo.proyeccion.remove()
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2, valores_matriz[indice], cmap=self.Colormap, vmin=-cota, vmax=cota)
                    lienzo.set_title(r'$r = %(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = 10)
            elif coordenada_fija == "phi":
                if cuadro == -1:
                    # Inicialización de la gráfica.
                    coordenada1, coordenada2 = np.meshgrid([0], [0])
                    Z = coordenada1**2+coordenada2**2
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
                elif 0 <= cuadro <= cuadro_fijo:
                    # Creación de la gráfica para el primer valor de la coordenada fija.
                    lienzo.proyeccion.remove()
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada2, valores_matriz[0].T[:cuadro*10+int(len(coordenada1)%10)].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
                elif cuadro_fijo < cuadro <= cuadro_fijo+longitud:
                    # Creación de la gráfica para los demás valores.
                    indice = cuadro-cuadro_fijo-1
                    lienzo.proyeccion.remove()
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2, valores_matriz[indice], cmap=self.Colormap, vmin=-cota, vmax=cota)
                    lienzo.set_title(r'$\phi = %(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = 10)
            elif coordenada_fija == "z":
                if cuadro == -1:
                    # Inicialización de la gráfica.
                    coordenada1, coordenada2 = np.meshgrid([0], [0, 1])
                    Z = 0*(coordenada1**2+coordenada2**2)
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada2, coordenada1, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
                elif 0 <= cuadro <= cuadro_fijo:
                    # Creación de la gráfica para el primer valor de la coordenada fija.
                    lienzo.proyeccion.remove()
                    if (cuadro == 0) and (int(len(coordenada1)%10) == 0):
                        coordenada1, coordenada2 = np.meshgrid([0], [0, 1])
                        Z = 0*(coordenada1**2+coordenada2**2)
                        lienzo.proyeccion = lienzo.pcolormesh(coordenada2, coordenada1, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
                    else:
                        lienzo.proyeccion = lienzo.pcolormesh(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada2, valores_matriz[0][:cuadro*10+int(len(coordenada1)%10)].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
                elif cuadro_fijo < cuadro <= cuadro_fijo+longitud:
                    # Creación de la gráfica para los demás valores.
                    indice = cuadro-cuadro_fijo-1
                    lienzo.proyeccion.remove()
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2, valores_matriz[indice].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
                    lienzo.set_title(r'$z =%(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = 10)        
        elif coordenadas == "Esféricas":
            if coordenada_fija == "theta":
                if cuadro == -1:
                    # Inicialización de la gráfica.
                    coordenada1, coordenada2 = np.meshgrid([0], [0])
                    Z = coordenada1**2+coordenada2**2
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
                elif 0 <= cuadro <= cuadro_fijo:
                    # Creación de la gráfica para el primer valor de la coordenada fija.
                    lienzo.proyeccion.remove()
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada2*np.sin((limites[1]-limites[0])*0/(longitud-1)+limites[0]), valores_matriz[0][:cuadro*10+int(len(coordenada1)%10)].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
                elif cuadro_fijo < cuadro <= cuadro_fijo+longitud:
                    # Creación de la gráfica para los demás valores.
                    indice = cuadro-cuadro_fijo-1
                    lienzo.proyeccion.remove()
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2*np.sin((limites[1]-limites[0])*indice/(longitud-1)+limites[0]), valores_matriz[indice].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
                    lienzo.set_title(r'$\theta = %(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = 10)
            elif coordenada_fija == "phi":
                if cuadro == -1:
                    # Inicialización de la gráfica.
                    coordenada1, coordenada2 = np.meshgrid([0], [0, 1])
                    Z = 0*(coordenada1**2+coordenada2**2)
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada2, coordenada1, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
                elif 0 <= cuadro <= cuadro_fijo:
                    # Creación de la gráfica para el primer valor de la coordenada fija.
                    lienzo.proyeccion.remove()
                    if (cuadro == 0) and (int(len(coordenada1)%10) == 0):
                        coordenada1, coordenada2 = np.meshgrid([0], [0, 1])
                        Z = 0*(coordenada1**2+coordenada2**2)
                        lienzo.proyeccion = lienzo.pcolormesh(coordenada2, coordenada1, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
                    else:
                        lienzo.proyeccion = lienzo.pcolormesh(coordenada1[:cuadro*10+int(len(coordenada1)%10)], coordenada2, valores_matriz[0][:cuadro*10+int(len(coordenada1)%10)].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
                elif cuadro_fijo < cuadro <= cuadro_fijo+longitud:
                    # Creación de la gráfica para los demás valores.
                    indice = cuadro-cuadro_fijo-1
                    lienzo.proyeccion.remove()
                    lienzo.proyeccion = lienzo.pcolormesh(coordenada1, coordenada2, valores_matriz[indice].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
                    lienzo.set_title(r'$z =%(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, pad = 10)
        return lienzo
    
    def actualizarProyeccion3D_especial(self, cuadro, cuadro_fijo, coordenada1, coordenada2, longitud, valores_matriz, limites, figura, cota):
        """
        Actualiza la proyección en problemas de tres dimensiones espaciales en coordenadas esféricas y radio como coordenada fija.
        
        Parámetros
        ----------
        cuadro: entero
            Cuadro actual de la animación.

        cuadro_fijo: entero
            Cuadro inicial del reproductor.

        coordenada1: lista flotantes
            Particion del dominio de la primera coordenada espacial.

        coordenada2: lista flotantes
            Particion del dominio de la segunda coordenada espacial.   

        longitud: entero
            Longitud de la partición de la coordenada fija.

        valores_matriz: arreglo bidimensional de flotantes
            Valores de la solución.

        limites: lista de dos flotantes
            Extremos del dominio de la coordenada fija.

        figura: Matplotlib.figure
            Figura que almacena los lienzos de las gráficas.
        
        cota: flotante
            Cota de valores de la solución.
        """

        self.valorespecial = False

        if cuadro == -1:
            # Inicialización de la gráfica.
            coordenada1, coordenada2 = np.meshgrid([0], [0])
            Z = coordenada1**2+coordenada2**2
            lienzo = figura.axes
            lienzo[0].proyeccion = lienzo[0].pcolormesh(coordenada1, coordenada2, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
            lienzo[1].proyeccion = lienzo[1].pcolormesh(coordenada1, coordenada2, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
            lienzo[0].grid(True)
            lienzo[1].grid(True)
            figura.txt = figura.text(0.4, 0.9, r'$r = %(valor)s $' % {"valor":0}, fontsize=15)
        elif 0 <= cuadro <= cuadro_fijo:
            # Creación de la gráfica para el primer valor de la coordenada fija.
            if (cuadro == 0) and (int(len(coordenada2)%10) == 0):
                lienzo = figura.axes
                lienzo[0].proyeccion.remove()
                lienzo[1].proyeccion.remove()
                coordenada1, coordenada2 = np.meshgrid([0], [0, 1])
                Z = 0*(coordenada1**2+coordenada2**2)
                lienzo[0].proyeccion = lienzo[0].pcolormesh(coordenada2, coordenada1, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
                lienzo[1].proyeccion = lienzo[1].pcolormesh(coordenada2, coordenada1, Z, cmap=self.Colormap, vmin=-cota, vmax=cota)
                lienzo[0].grid(True)
                lienzo[1].grid(True)
            else:
                lienzo = figura.axes
                lienzo[0].proyeccion.remove()
                lienzo[1].proyeccion.remove()
                r = np.linspace(0, 0, int(np.ceil(len(coordenada1)/2)))
                lienzo[0].grid(False)
                lienzo[1].grid(False)
                lienzo[0].proyeccion = lienzo[0].pcolormesh(coordenada2[:cuadro*10+int(len(coordenada2)%10)], r, valores_matriz[0][:cuadro*10+int(len(coordenada2)%10)].T[:int(np.ceil(len(coordenada1)/2))], cmap=self.Colormap, vmin=-cota, vmax=cota)
                lienzo[1].proyeccion = lienzo[1].pcolormesh(coordenada2[:cuadro*10+int(len(coordenada2)%10)], r, np.flip(valores_matriz[0][:cuadro*10+int(len(coordenada2)%10)].T[int(np.floor(len(coordenada1)/2)):],1), cmap=self.Colormap, vmin=-cota, vmax=cota)
        elif cuadro_fijo < cuadro <= cuadro_fijo+longitud:
            # Creación de la gráfica para los demás valores.
            lienzo = figura.axes
            indice = cuadro-cuadro_fijo-1
            lienzo[0].proyeccion.remove()
            lienzo[1].proyeccion.remove()
            lienzo[0].grid(False)
            lienzo[1].grid(False)
            figura.txt.remove()
            r = np.linspace(0, np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2), int(np.ceil(len(coordenada1)/2)))
            r1, phi1 = np.meshgrid(r,  coordenada2)
            lienzo[0].proyeccion = lienzo[0].pcolormesh(phi1, r1, valores_matriz[indice].T[:int(np.ceil(len(coordenada1)/2))].T, cmap=self.Colormap, vmin=-cota, vmax=cota)
            lienzo[1].proyeccion = lienzo[1].pcolormesh(phi1, r1, np.flip(valores_matriz[indice].T[int(np.floor(len(coordenada1)/2)):].T, 1), cmap=self.Colormap, vmin=-cota, vmax=cota)
            figura.txt = figura.text(0.4, 0.9, r'$r = %(valor)s $' % {"valor":np.round((limites[1]-limites[0])*indice/(longitud-1)+limites[0], 2)}, fontsize=15)
            lienzo[0].grid(True)
            lienzo[1].grid(True)
        return lienzo[0], lienzo[1]
    
    def calculoEtiquetasRadianes(self, angulo, valornulo1):
        """
        Convierte el ángulo en grados a radianes y crea un string con formato LaTeX para representar el ángulo.
        
        Parámetros
        ----------
        angulo: flotante
            Ángulo en grados.

        **valornulo1** 
            Son argumentos necesarios para evitar conflictos entre funciones.

        Salida
        ----------
        angulo_string: string
            String con el ángulo en formato LaTeX y en radianes. 
        """

        # Esta función fue tomada y modificada de Krupip. (20 de junio de 2017). Respuesta a la pregunta "How to set the format for *all* matplotlib polar axis angular labels to be in terms of pi and radians?". stackoverflow. https://stackoverflow.com/a/44659713
        # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 3.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/3.0/
        # La modificación consiste en la modificación de la función para que exprese fracciones en lugar de números decimales.

        angulo_radianes = angulo/np.pi
        if angulo_radianes == float(1):
            # Si el ángulo es de pi radianes.
            angulo_radianes = "\pi"
        elif angulo_radianes == float(0):
            # Si el ángulo es cero.
            angulo_radianes = "0"
        else:
            # Si el ángulo es cualquier otro.
            
            # La conversión a fracción fue tomada de Pieters, Martijn. (28 de abril de 2024). Respuesta a la pregunta "How to convert a decimal number into fraction?". stackoverflow. https://stackoverflow.com/a/23344270 
            # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 3.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/3.0/
            angulo_radianes = Fraction(angulo_radianes).limit_denominator()

            angulo_radianes = "\\frac{"+"{0}".format(angulo_radianes.numerator if angulo_radianes.numerator != 1 else "")+"\pi}{"+"{0}".format(angulo_radianes.denominator)+"}"
        angulo_string = r"$"+r"{}".format(angulo_radianes)+r"$"
        return angulo_string

    def crearGrafica1D(self, canva):
        """
        Diseño de la gráfica para problemas con una dimensión espacial y dependencia temporal.

        Parámetros
        ----------
        canva: Matplotlib.figure
            Figura de Matplotlib que contiene la gráfica.

        Salida
        ----------
        [x, segmentos, tiempo_maximo, resolucion]

            x: lista de flotantes
                Partición del dominio en x.

            segmentos: lista de segmentos
                Segmentos que conforman la gráfica.

            tiempo_maximo: flotante
                Tiempo máximo hasta el que se calculará la solución.

            resolucion: entero
                FPS de la animación.
        """

        self.dominio = [float(self.Dominio[0][0]), float(self.Dominio[0][1]), float(self.Dominio[-1][0])]
        self.Cota = max(abs(self.minimo-(self.maximo-self.minimo)*0.05), abs(self.maximo+(self.maximo-self.minimo)*0.05))
        resolucion = 25

        canva.axes = canva.figura.add_subplot()
        canva.axes.set_position([0.15, 0.2, 0.65, 0.65])
        canva.axes.set_xlim(self.dominio[0], self.dominio[1])
        canva.axes.set_ylim(self.minimo-(self.maximo-self.minimo)*0.05, self.maximo+(self.maximo-self.minimo)*0.05)
        canva.axes.grid(True, lw=0.5, alpha=0.2, color="black")
        canva.axes.set_facecolor((0.52, 0.50, 0.49, 0.3))

        # La configuración para colocar los textos de las leyendas de los ejes (de cualquiera de las gráficas) en negritas fue tomada de JonnDough. (27 de mayo de 2022). Respuesta a la pregunta "Bold font weight for LaTeX axes label in matplotlib". stackoverflow. https://stackoverflow.com/a/72401194
        # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 4.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/4.0/ 
        canva.axes.set_xlabel(r"$\bf{x}$")

        canva.axes.set_ylabel(r"$\bf{u(x,t)}$")
        canva.axes.set_title(' Tiempo \n{:02d}:{:02d}.{:02d}'.format(0, 0, 0), pad = 10)

        # Esta línea de código fue modificada de unutbu. (18 de marzo de 2016). Respuesta a la pregunta "python matplotlib with a line color gradient and colorbar". stackoverflow. https://stackoverflow.com/a/36074775
        # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 3.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/3.0/
        solucion = LineCollection(self.Segmentos[0], cmap=self.Colormap, norm=plt.Normalize(-self.Cota, self.Cota), array = self.MatrizResultados[0], linewidth = 3)
        canva.axes.add_collection(solucion)
        solucion.set_segments([])
        
        return [self.Dominios[0], solucion, self.dominio[-1], resolucion]
    
    def crearProyeccion1D(self, canva):
        """
        Diseño de la proyección para problemas con una dimensión espacial y dependencia temporal.

        Parámetros
        ----------
        canva: Matplotlib.figure
            Figura de Matplotlib que contiene la gráfica.

        Salida
        ----------
        [x, t, tiempo_maximo, resolucion]

            x: lista de flotantes
                Partición del dominio en x.

            t: lista de flotantes
                Partición del dominio en t.

            tiempo_maximo: flotante
                Tiempo máximo hasta el que se calculará la solución.

            resolucion: entero
                FPS de la animación.
        """

        self.dominio = [float(self.Dominio[0][0]), float(self.Dominio[0][1]), float(self.Dominio[-1][0])]
        self.Cota = max(abs(self.minimo-(self.maximo-self.minimo)*0.05), abs(self.maximo+(self.maximo-self.minimo)*0.05))
        resolucion = 25

        canva.axes = canva.figura.add_subplot()
        canva.axes.set_position([0.15, 0.2, 0.65, 0.65])
        canva.axes.set_xlim(0, self.dominio[-1])
        canva.axes.set_ylim(self.dominio[0]-0.0125, self.dominio[1]+0.0125)
        canva.axes.set_facecolor((0.52, 0.50, 0.49, 0.3))
        canva.axes.set_xlabel(r"$\bf{t}$")
        canva.axes.set_ylabel(r"$\bf{x}$")

        self.x, self.T = np.meshgrid(self.Dominios[0], self.t_grid)
        
        return [self.Dominios[0], self.t_grid, self.dominio[-1], resolucion]
    
    def crearGrafica2D_cartesianas(self, canva):
        """
        Diseño de la gráfica para problemas con dos dimensiones espaciales en coordenadas cartesianas.

        Parámetros
        ----------
        canva: Matplotlib.figure
            Figura de Matplotlib que contiene la gráfica.

        Salida
        ----------
        [x, y, tiempo_maximo, resolucion]

            x: Numpy meshgrid
                Meshgrid de la primera coordenada.

            y: Numpy meshgrid
                Meshgrid de la segunda coordenada.

            tiempo_maximo: flotante
                Tiempo máximo hasta el que se calculará la solución.

            resolucion: entero
                FPS de la animación.
        """

        self.dominio = [float(self.Dominio[0][0]), float(self.Dominio[0][1]), float(self.Dominio[1][0]), float(self.Dominio[1][1]), float(self.Dominio[-1][0])]
        self.Cota = max(abs(self.minimo-(self.maximo-self.minimo)*0.05), abs(self.maximo+(self.maximo-self.minimo)*0.05))
        resolucion = 25

        canva.axes = canva.figura.add_subplot(projection='3d')
        canva.axes.set_position([0.05, 0.15, 0.8, 0.8])
        canva.axes.set_xlim(self.dominio[0], self.dominio[1])
        canva.axes.set_ylim(self.dominio[2], self.dominio[3])
        canva.axes.set_zlim(self.minimo-(self.maximo-self.minimo)*0.05, self.maximo+(self.maximo-self.minimo)*0.05)
        canva.axes.xaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.yaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.zaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.set_box_aspect([1,1,1])
        canva.axes.set_xlabel(r"$\bf{x}$")
        canva.axes.set_ylabel(r"$\bf{y}$")
        canva.axes.set_zlabel(r"$\bf{u(x,y)}$")
        if self.dependencia_tiempo:
            canva.axes.set_title(' Tiempo \n{:02d}:{:02d}.{:02d}'.format(0, 0, 0), pad = -10)

        self.x, self.y = np.meshgrid(self.Dominios[0], self.Dominios[1])

        return [self.x, self.y, self.dominio[-1], resolucion]
    
    def crearProyeccion2D_cartesianas(self, canva):
        """
        Diseño de la proyección para problemas con dos dimensiones espaciales en coordenadas cartesianas.

        Parámetros
        ----------
        canva: Matplotlib.figure
            Figura de Matplotlib que contiene la gráfica.

        Salida
        ----------
        [x, t, tiempo_maximo, resolucion]

            x: lista de flotantes
                Partición del dominio en x.

            y: lista de flotantes
                Partición del dominio en y.

            tiempo_maximo: flotante
                Tiempo máximo hasta el que se calculará la solución.

            resolucion: entero
                FPS de la animación.
        """

        self.dominio = [float(self.Dominio[0][0]), float(self.Dominio[0][1]), float(self.Dominio[1][0]), float(self.Dominio[1][1]), float(self.Dominio[-1][0])]
        self.Cota = max(abs(self.minimo-(self.maximo-self.minimo)*0.05), abs(self.maximo+(self.maximo-self.minimo)*0.05))
        resolucion = 25

        canva.axes = canva.figura.add_subplot()
        canva.axes.set_position([0.15, 0.2, 0.65, 0.65])
        canva.axes.set_xlim(self.dominio[0], self.dominio[1])
        canva.axes.set_ylim(self.dominio[2], self.dominio[3])
        canva.axes.set_facecolor((0.52, 0.50, 0.49, 0.3))
        canva.axes.set_xlabel(r"$\bf{x}$")
        canva.axes.set_ylabel(r"$\bf{y}$")
        if self.dependencia_tiempo:
            canva.axes.set_title(' Tiempo \n{:02d}:{:02d}.{:02d}'.format(0, 0, 0), pad = -10)

        self.x, self.y = np.meshgrid(self.Dominios[0], self.Dominios[1])
        
        return [self.Dominios[0], self.Dominios[1], self.dominio[-1], resolucion]

    def crearGrafica2D_polares(self, canva):
        """
        Diseño de la gráfica para problemas con dos dimensiones espaciales en coordenadas cartesianas.

        Parámetros
        ----------
        canva: Matplotlib.figure
            Figura de Matplotlib que contiene la gráfica.

        Salida
        ----------
        [x, y, tiempo_maximo, resolucion]

            x: Numpy meshgrid
                Meshgrid de la coordenada x.

            y: Numpy meshgrid
                Meshgrid de la coordenada y.

            tiempo_maximo: flotante
                Tiempo máximo hasta el que se calculará la solución.

            resolucion: entero
                FPS de la animación.
        """

        self.dominio = [float(self.Dominio[0][0]), float(self.Dominio[0][1]), float(self.Dominio[1][0]), float(self.Dominio[1][1]), float(self.Dominio[-1][0])]
        self.Cota = max(abs(self.minimo-(self.maximo-self.minimo)*0.05), abs(self.maximo+(self.maximo-self.minimo)*0.05))
        resolucion = 25

        self.u, self.v = np.meshgrid(self.Dominios[0], self.Dominios[1])
        self.x, self.y = self.u*np.cos(self.v), self.u*np.sin(self.v)

        canva.axes = canva.figura.add_subplot(projection='3d')
        canva.axes.set_position([0.05, 0.15, 0.8, 0.8])
        canva.axes.set_xlim(np.min(self.x), np.max(self.x))
        canva.axes.set_ylim(np.min(self.y), max(np.max(self.y), np.max(self.x)))
        canva.axes.set_zlim(self.minimo-(self.maximo-self.minimo)*0.05, self.maximo+(self.maximo-self.minimo)*0.05)
        canva.axes.xaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.yaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.zaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.set_box_aspect([1,1,1])
        canva.axes.set_xlabel(r"$\bf{x}$")
        canva.axes.set_ylabel(r"$\bf{y}$")
        canva.axes.set_zlabel(r"$\bf{u(r,\phi)}$")
        if self.dependencia_tiempo:
            canva.axes.set_title(' Tiempo \n{:02d}:{:02d}.{:02d}'.format(0, 0, 0), pad = -10)

        return [self.x, self.y, self.dominio[-1], resolucion]
    
    def crearProyeccion2D_polares(self, canva):
        """
        Diseño de la gráfica para problemas con dos dimensiones espaciales en coordenadas cartesianas.

        Parámetros
        ----------
        canva: Matplotlib.figure
            Figura de Matplotlib que contiene la gráfica.

        Salida
        ----------
        [phi, r, tiempo_maximo, resolucion]

            phi: lista de flotantes
                Partición del dominio de la coordenada phi.

            r: lista de flotantes
                Partición del dominio de la coordenada r.

            tiempo_maximo: flotante
                Tiempo máximo hasta el que se calculará la solución.

            resolucion: entero
                FPS de la animación.
        """

        self.dominio = [float(self.Dominio[0][0]), float(self.Dominio[0][1]), float(self.Dominio[1][0]), float(self.Dominio[1][1]), float(self.Dominio[-1][0])]
        # Determinación del número de puntos en los que se divide el eje angular.
        if self.dominio[3] <= np.pi/2:
            number = 5
        elif np.pi/2 < self.dominio[3] <= 3*np.pi/2:
            number = 7
        else:
            number = 9
        self.Cota = max(abs(self.minimo-(self.maximo-self.minimo)*0.05), abs(self.maximo+(self.maximo-self.minimo)*0.05))
        resolucion = 25

        canva.axes = canva.figura.add_subplot(projection='polar')
        canva.axes.set_position([0.15, 0.2, 0.65, 0.65])
        canva.axes.set_xlim(0, self.dominio[3])
        canva.axes.set_ylim(0, self.dominio[1])
        canva.axes.set_facecolor((0.52, 0.50, 0.49, 0.3))

        # Diseño de las etiquetas angulares en el gráfico en coordenadas polares.
        thetagrid = np.linspace(0, self.dominio[3]*180/np.pi, number)
        canva.axes.set_thetagrids(thetagrid if self.dominio[3] != 2*np.pi else thetagrid[:-1])

        # La configuración para expresar en radianes las leyendas del eje angular en gráficos polares fue tomada y modificada de Krupip. (20 de junio de 2017). Respuesta a la pregunta "How to set the format for *all* matplotlib polar axis angular labels to be in terms of pi and radians?". stackoverflow. https://stackoverflow.com/a/44659713
        # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 3.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/3.0/
        # La modificación consiste en la modificación de la función que se pasa a FuncFormatter para que exprese fracciones en lugar de números decimales.
        canva.axes.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(self.calculoEtiquetasRadianes))
         # Diseño de las etiquetas radiales en el gráfico en coordenadas polares.
        canva.axes.set_rlabel_position(25)
        canva.axes.set_yticks(np.arange(self.dominio[0], self.dominio[1]+(self.dominio[1]-self.dominio[0])/10, (self.dominio[1]-self.dominio[0])/5)[1:])

        canva.axes.grid(lw=0.2)
        if self.dependencia_tiempo:
            canva.axes.set_title(' Tiempo \n{:02d}:{:02d}.{:02d}'.format(0, 0, 0), pad = -10)

        # El procesamiento de los datos para la creación de una gráfica en coordenadas polares se basó en Wilson, R. (24 de febrero de 2012). Producing polar contour plots with matplotlib. Robin's blog. https://blog.rtwilson.com/producing-polar-contour-plots-with-matplotlib/
        self.u, self.v = np.meshgrid(self.Dominios[0], self.Dominios[1])
        self.x, self.y = self.v, self.u
        
        return [self.Dominios[1], self.Dominios[0], self.dominio[-1], resolucion]
    
    def crearGrafica3D_cartesianas(self, canva, coordenada):
        """
        Diseño de la gráfica para problemas con tres dimensiones espaciales en coordenadas cartesianas.

        Parámetros
        ----------
        canva: Matplotlib.figure
            Figura de Matplotlib que contiene la gráfica.

        coordenada: string
            Coordenada fija de la solución.

        Salida
        ----------
        [longitud, resolucion]

            longitud: entero
                Longitud de la partición de la coordenada fija.

            resolucion: entero
                Resolucion temporal de la animación.
        """

        self.dominio = [float(self.Dominio[0][0]), float(self.Dominio[0][1]), float(self.Dominio[1][0]), float(self.Dominio[1][1]), float(self.Dominio[-1][0]), float(self.Dominio[-1][1])]
        self.Cota = max(abs(self.minimo-(self.maximo-self.minimo)*0.05), abs(self.maximo+(self.maximo-self.minimo)*0.05))
        resolucion = 25

        canva.axes = canva.figura.add_subplot(1, 1, 1, projection='3d')
        canva.axes.set_position([0.05, 0.15, 0.8, 0.8])
        canva.axes.set_xlim(self.dominio[0], self.dominio[1])
        canva.axes.set_ylim(self.dominio[2], self.dominio[3])
        canva.axes.set_zlim(self.dominio[4], self.dominio[5])
        canva.axes.xaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.yaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.zaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.set_box_aspect([1,1,1])
        canva.axes.view_init(elev=30, azim=45)
        canva.axes.set_xlabel(r"$\bf{x}$")
        canva.axes.set_ylabel(r"$\bf{y}$")
        canva.axes.set_zlabel(r"$\bf{z}$")

        # Diseño y determinación de parámetros importantes dependiendo de la coordenada fija. Se establecen los meshgrids a utilizar para crear la gráfica y la longitud de la partición del dominio de la coordenada fija.
        if coordenada == "x":
            self.x, self.y = np.meshgrid(self.Dominios[1], self.Dominios[2])
            longitud = len(self.Dominios[0])
            canva.axes.set_title(r'$x=%(valor)s$' % {"valor":self.dominio[0]}, pad = -10)
        elif coordenada == "y":
            self.x, self.y = np.meshgrid(self.Dominios[0], self.Dominios[2])
            longitud = len(self.Dominios[1])
            canva.axes.set_title(r'$y=%(valor)s$' % {"valor":self.dominio[0]}, pad = -10)
        elif coordenada == "z":
            self.x, self.y = np.meshgrid(self.Dominios[0], self.Dominios[1])
            longitud = len(self.Dominios[2])
            canva.axes.set_title(r'$z=%(valor)s$' % {"valor":self.dominio[0]}, pad = -10)

        # Creación del paralelípedo para visualizar la forma del objeto de acuerdo a los dominios introducidos.
        x = np.linspace(self.dominio[0], self.dominio[1], 2)
        y = np.linspace(self.dominio[2], self.dominio[3], 2)
        z = np.linspace(self.dominio[4], self.dominio[5], 2)
        xw , yw = np.meshgrid(x, y)
        yw2 , zw = np.meshgrid(y, z)
        xw2 , zw2 = np.meshgrid(x, z)
        Carazd = self.dominio[4]*(xw+yw)
        Carazu = self.dominio[5]+0*(xw+yw)
        Caraxd = self.dominio[0]*(yw2+zw)
        Caraxu = self.dominio[1]+0*(yw2+zw)
        Carayd = self.dominio[2]*(xw2+zw2)
        Carayu = self.dominio[3]+0*(xw2+zw2)
        canva.axes.plot_wireframe(xw, yw, Carazu, lw = 0.5, color="black", alpha = 0.3)
        canva.axes.plot_wireframe(xw, yw, Carazd, lw = 0.5, color="black", alpha = 0.3)
        canva.axes.plot_wireframe(Caraxd, yw2, zw2, lw = 0.5, color="black", alpha = 0.3)
        canva.axes.plot_wireframe(Caraxu, yw2, zw2, lw = 0.5, color="black", alpha = 0.3)
        canva.axes.plot_wireframe(xw2, Carayd, zw2, lw = 0.5, color="black", alpha = 0.3)
        canva.axes.plot_wireframe(xw2, Carayu, zw2, lw = 0.5, color="black", alpha = 0.3)
        canva.axes.plot_surface(xw, yw, Carazu, lw = 0.5, color="black", alpha = 0.07)
        canva.axes.plot_surface(xw, yw, Carazd, lw = 0.5, color="black", alpha = 0.07)
        canva.axes.plot_surface(Caraxd, yw2, zw2, lw = 0.5, color="black", alpha = 0.07)
        canva.axes.plot_surface(Caraxu, yw2, zw2, lw = 0.5, color="black", alpha = 0.07)
        canva.axes.plot_surface(xw2, Carayd, zw2, lw = 0.5, color="black", alpha = 0.07)
        canva.axes.plot_surface(xw2, Carayu, zw2, lw = 0.5, color="black", alpha = 0.07)

        return [longitud, resolucion]

    def crearProyeccion3D_cartesianas(self, canva, coordenada):
        """
        Diseño de la proyección para problemas con tres dimensiones espaciales en coordenadas cartesianas.

        Parámetros
        ----------
        canva: Matplotlib.figure
            Figura de Matplotlib que contiene la gráfica.

        coordenada: string
            Coordenada fija de la solución.

        Salida
        ----------
        [abcisa, ordenada, coordenada_fija, longitud, resolucion]

            abcisa: lista flotantes
                Partición de la coordenada que funcionará como eje de abcisas.

            ordenada: lista flotantes
                Partición de la coordenada que funcionará como eje de ordenadas.

            coordenada_fija: string
                Coordenada fija.

            longitud: entero
                Longitud de la partición de la coordenada fija.

            resolucion: entero
                Resolucion temporal de la animación.
        """

        self.dominio = [float(self.Dominio[0][0]), float(self.Dominio[0][1]), float(self.Dominio[1][0]), float(self.Dominio[1][1]), float(self.Dominio[-1][0]), float(self.Dominio[-1][1])]
        self.Cota = max(abs(self.minimo-(self.maximo-self.minimo)*0.05), abs(self.maximo+(self.maximo-self.minimo)*0.05))
        resolucion = 25

        canva.axes = canva.figura.add_subplot()
        canva.axes.set_position([0.13, 0.2, 0.65, 0.65])
        canva.axes.set_facecolor((0.52, 0.50, 0.49, 0.3))
        canva.axes.set_title(r'${%(coordenada)s} = {%(valor)s}$' % {'coordenada': coordenada, 'valor': self.dominio[0]}, pad = 10) 
        if coordenada == "x":
            # Diseño del lienzo.
            canva.axes.set_xlim(self.dominio[2], self.dominio[3])
            canva.axes.set_ylim(self.dominio[4], self.dominio[5])
            canva.axes.set_xlabel(r"$\bf{y}$")
            canva.axes.set_ylabel(r"$\bf{z}$") 

            # Variables de ayuda para la graficación y animación.
            self.v, self.u = np.meshgrid(self.Dominios[1], self.Dominios[2])
            self.x, self.y = np.meshgrid(self.Dominios[1], self.Dominios[2])
            abcisa = self.Dominios[1]
            ordenada = self.Dominios[2]
            longitud = len(self.Dominios[0])
        elif coordenada == "y":
            # Diseño del lienzo.
            canva.axes.set_xlim(self.dominio[0], self.dominio[1])
            canva.axes.set_ylim(self.dominio[4], self.dominio[5])
            canva.axes.set_xlabel(r"$\bf{x}$")
            canva.axes.set_ylabel(r"$\bf{z}$")

            # Variables de ayuda para la graficación y animación.
            self.v, self.u = np.meshgrid(self.Dominios[0], self.Dominios[2])
            self.x, self.y = np.meshgrid(self.Dominios[0], self.Dominios[2])
            abcisa = self.Dominios[0]
            ordenada = self.Dominios[2]
            longitud = len(self.Dominios[1])
        elif coordenada == "z":
            # Diseño del lienzo.
            canva.axes.set_xlim(self.dominio[0], self.dominio[1])
            canva.axes.set_ylim(self.dominio[2], self.dominio[3])
            canva.axes.set_xlabel(r"$\bf{x}$")
            canva.axes.set_ylabel(r"$\bf{y}$")

            # Variables de ayuda para la graficación y animación.
            self.v, self.u = np.meshgrid(self.Dominios[0], self.Dominios[2])
            self.x, self.y = np.meshgrid(self.Dominios[0], self.Dominios[1])
            abcisa = self.Dominios[0]
            ordenada = self.Dominios[1]
            longitud = len(self.Dominios[2])
        
        return [abcisa, ordenada, coordenada, longitud, resolucion]
    
    def crearGrafica3D_cilindricas(self, canva, coordenada):
        """
        Diseño de la gráfica para problemas con tres dimensiones espaciales en coordenadas cilindricas.

        Parámetros
        ----------
        canva: Matplotlib.figure
            Figura de Matplotlib que contiene la gráfica.

        coordenada: string
            Coordenada fija de la solución.

        Salida
        ----------
        [longitud, resolucion]

            longitud: entero
                Longitud de la partición de la coordenada fija.

            resolucion: entero
                Resolucion temporal de la animación.
        """

        self.dominio = [float(self.Dominio[0][0]), float(self.Dominio[0][1]), float(self.Dominio[1][0]), float(self.Dominio[1][1]), float(self.Dominio[-1][0]), float(self.Dominio[-1][1])]
        self.Cota = max(abs(self.minimo-(self.maximo-self.minimo)*0.05), abs(self.maximo+(self.maximo-self.minimo)*0.05))
        resolucion = 25
        
        canva.axes = canva.figura.add_subplot(projection='3d')
        canva.axes.set_position([0.05, 0.15, 0.8, 0.8])
        r2, phi2 = np.meshgrid(self.Dominios[0], self.Dominios[1])
        x, y = r2*np.cos(phi2), r2*np.sin(phi2)
        canva.axes.set_xlim(x.min(), x.max())
        canva.axes.set_ylim(y.min(), y.max())
        canva.axes.set_zlim(self.dominio[4], self.dominio[5])
        canva.axes.xaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.yaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.zaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.set_box_aspect([1,1,1])
        canva.axes.view_init(elev=30, azim=45)
        canva.axes.set_xlabel(r"$\bf{x}$")
        canva.axes.set_ylabel(r"$\bf{y}$")
        canva.axes.set_zlabel(r"$\bf{z}$")

        # Diseño y determinación de parámetros importantes dependiendo de la coordenada fija. Se establecen los meshgrids a utilizar para crear la gráfica y la longitud de la partición del dominio de la coordenada fija.
        if coordenada == "r":
            self.x, self.y = np.meshgrid(self.Dominios[1], self.Dominios[2])
            longitud = len(self.Dominios[0])
            canva.axes.set_title(r'$r=%(valor)s$' % {"valor":self.dominio[0]}, pad = -10)
        elif coordenada == "phi":
            self.x, self.y = np.meshgrid(self.Dominios[0], self.Dominios[2])
            longitud = len(self.Dominios[1])
            canva.axes.set_title(r'$\phi=%(valor)s$' % {"valor":self.dominio[2]}, pad = -10)
        elif coordenada == "z":
            self.u, self.v = np.meshgrid(self.Dominios[0], self.Dominios[1])
            self.x, self.y = self.u*np.cos(self.v), self.u*np.sin(self.v)
            longitud = len(self.Dominios[2])
            canva.axes.set_title(r'$z=%(valor)s$' % {"valor":self.dominio[4]}, pad = -10)

        # Creación del cilindro para visualizar la forma del objeto de acuerdo a los dominios introducidos.
        r = np.linspace(self.dominio[0], self.dominio[1], 2)
        p = np.linspace(self.dominio[2], self.dominio[3], 50)
        z = np.linspace(self.dominio[4], self.dominio[5], 2)
        rw, pw = np.meshgrid(r, p)
        pw2, zw = np.meshgrid(p, z)
        xw, yw = self.dominio[1]*np.cos(pw2), self.dominio[1]*np.sin(pw2)
        xw2, yw2 = rw*np.cos(pw), rw*np.sin(pw)
        xw3, yw3 = self.dominio[1]*np.cos(p), self.dominio[1]*np.sin(p)
        Carazd = self.dominio[4]+0*(xw2+yw2)
        Carazu = self.dominio[5]+0*(xw2+yw2)
        canva.axes.plot(xw3.T, yw3.T, zs=self.dominio[5], lw = 0.5, color="black", alpha = 0.3)
        canva.axes.plot(xw3.T, yw3.T, zs=self.dominio[4], lw = 0.5, color="black", alpha = 0.3)
        canva.axes.plot_surface(xw2, yw2, Carazu, lw = 0.5, color="black", alpha = 0.07)
        canva.axes.plot_surface(xw2, yw2, Carazd, lw = 0.5, color="black", alpha = 0.07)
        canva.axes.plot_surface(xw, yw, zw, lw = 0.5, color="black", alpha = 0.07)

        return [longitud, resolucion]

    def crearProyeccion3D_cilindricas(self, canva, coordenada):
        """
        Diseño de la proyección para problemas con tres dimensiones espaciales en coordenadas cilindricas.

        Parámetros
        ----------
        canva: Matplotlib.figure
            Figura de Matplotlib que contiene la gráfica.

        coordenada: string
            Coordenada fija de la solución.

        Salida
        ----------
        [abcisa, ordenada, coordenada_fija, longitud, resolucion]

            abcisa: lista flotantes
                Partición de la coordenada que funcionará como eje de abcisas.

            ordenada: lista flotantes
                Partición de la coordenada que funcionará como eje de ordenadas.

            coordenada_fija: string
                Coordenada fija.

            longitud: entero
                Longitud de la partición de la coordenada fija.

            resolucion: entero
                Resolucion temporal de la animación.
        """

        self.dominio = [float(self.Dominio[0][0]), float(self.Dominio[0][1]), float(self.Dominio[1][0]), float(self.Dominio[1][1]), float(self.Dominio[-1][0]), float(self.Dominio[-1][1])]
        self.Cota = max(abs(self.minimo-(self.maximo-self.minimo)*0.05), abs(self.maximo+(self.maximo-self.minimo)*0.05))
        resolucion = 25

        if coordenada == "r":
            # Diseño del lienzo.
            canva.axes = canva.figura.add_subplot()
            canva.axes.set_xlim(0, self.dominio[3])
            canva.axes.set_ylim(self.dominio[4], self.dominio[5])
            canva.axes.set_xlabel(r"$\bf{\phi}$")
            canva.axes.set_ylabel(r"$\bf{z}$")
            canva.axes.set_title(r'$r = %(valor)s$' % {"valor":self.dominio[0]}, pad = 10) 

            # Variables de ayuda para la graficación y animación.
            self.v, self.u = np.meshgrid(self.Dominios[1], self.Dominios[2])

            abcisa = self.Dominios[1]
            ordenada = self.Dominios[2]
            longitud = len(self.Dominios[0])
        elif coordenada == "phi":
            # Diseño del lienzo.
            canva.axes = canva.figura.add_subplot()
            canva.axes.set_xlim(self.dominio[0], self.dominio[1])
            canva.axes.set_ylim(self.dominio[4], self.dominio[5])
            canva.axes.set_xlabel(r"$\bf{r}$")
            canva.axes.set_ylabel(r"$\bf{z}$")
            canva.axes.set_title(r'$\phi=%(valor)s$' % {"valor":self.dominio[2]}, pad = 10) 

            # Variables de ayuda para la graficación y animación.
            self.v, self.u = np.meshgrid(self.Dominios[0], self.Dominios[2])
            abcisa = self.Dominios[0]
            ordenada = self.Dominios[2]
            longitud = len(self.Dominios[1])
        elif coordenada == "z":
            # Diseño del lienzo.
            canva.axes = canva.figura.add_subplot(projection='polar')
            canva.axes.set_xlim(0, self.dominio[3])
            canva.axes.set_ylim(0, self.dominio[1])
            canva.axes.set_title(r'$z=%(valor)s$' % {"valor":self.dominio[4]}, pad = 10) 
            # Determinación del número de puntos en los que se divide el eje angular.
            if self.dominio[3] <= np.pi/2:
                number = 5
            elif np.pi/2 < self.dominio[3] <= 3*np.pi/2:
                number = 7
            else:
                number = 9

            # Diseño de las etiquetas angulares.
            thetagrid = np.linspace(0, self.dominio[3]*180/np.pi, number)
            canva.axes.set_thetagrids(thetagrid if self.dominio[3] != 2*np.pi else thetagrid[:-1])
            canva.axes.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(self.calculoEtiquetasRadianes))

            # Diseño de las etiquetas radiales.
            canva.axes.set_rlabel_position(25)
            canva.axes.set_yticks(np.arange(self.dominio[0], self.dominio[1]+(self.dominio[1]-self.dominio[0])/10, (self.dominio[1]-self.dominio[0])/5)[1:])
            canva.axes.grid(lw=0.2)

            # Variables de ayuda para la graficación y animación.
            # El procesamiento de los datos para la creación de una gráfica de proyección de z en coordenadas cilíndricas se basó en Wilson, R. (24 de febrero de 2012). Producing polar contour plots with matplotlib. Robin's blog. https://blog.rtwilson.com/producing-polar-contour-plots-with-matplotlib/
            self.u, self.v = np.meshgrid(self.Dominios[0], self.Dominios[1])
            abcisa = self.Dominios[1]
            ordenada = self.Dominios[0]
            longitud = len(self.Dominios[2])
        canva.axes.set_position([0.15, 0.2, 0.65, 0.65])
        canva.axes.set_facecolor((0.52, 0.50, 0.49, 0.3))
        
        return [abcisa, ordenada, coordenada, longitud, resolucion]
    
    def crearGrafica3D_esfericas(self, canva, coordenada):
        """
        Diseño de la gráfica para problemas con tres dimensiones espaciales en coordenadas esféricas.

        Parámetros
        ----------
        canva: Matplotlib.figure
            Figura de Matplotlib que contiene la gráfica.

        coordenada: string
            Coordenada fija de la solución.

        Salida
        ----------
        [longitud, resolucion]

            longitud: entero
                Longitud de la partición de la coordenada fija.

            resolucion: entero
                Resolucion temporal de la animación.
        """

        self.dominio = [float(self.Dominio[0][0]), float(self.Dominio[0][1]), float(self.Dominio[1][0]), float(self.Dominio[1][1]), float(self.Dominio[-1][0]), float(self.Dominio[-1][1])]
        self.Cota = max(abs(self.minimo-(self.maximo-self.minimo)*0.05), abs(self.maximo+(self.maximo-self.minimo)*0.05))
        resolucion = 25

        canva.axes = canva.figura.add_subplot(projection='3d')
        canva.axes.set_position([0.05, 0.15, 0.8, 0.8])
        canva.axes.xaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.yaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.zaxis.set_pane_color((0.52, 0.50, 0.49, 1.0))
        canva.axes.set_box_aspect([1,1,1])
        canva.axes.view_init(elev=30, azim=45)
        canva.axes.set_xlabel(r"$\bf{x}$")
        canva.axes.set_ylabel(r"$\bf{y}$")
        canva.axes.set_zlabel(r"$\bf{z}$")

        # Diseño y determinación de parámetros importantes dependiendo de la coordenada fija. Se establecen los meshgrids a utilizar para crear la gráfica y la longitud de la partición del dominio de la coordenada fija.
        if coordenada == "r":
            self.x, self.y = np.meshgrid(self.Dominios[1], self.Dominios[2])
            longitud = len(self.Dominios[0])
            canva.axes.set_title(r'$r=%(valor)s$' % {"valor":self.dominio[0]}, pad = -10)
        elif coordenada == "theta":
            self.x, self.y = np.meshgrid(self.Dominios[0], self.Dominios[2])
            longitud = len(self.Dominios[1])
            canva.axes.set_title(r'$\theta=%(valor)s$' % {"valor":self.dominio[2]}, pad = -10)
        elif coordenada == "phi":
            self.x, self.y = np.meshgrid(self.Dominios[0], self.Dominios[1])
            longitud = len(self.Dominios[2])
            canva.axes.set_title(r'$\phi=%(valor)s$' % {"valor":self.dominio[4]}, pad = -10)

        # Creación de la esfera para visualizar la forma del objeto de acuerdo a los dominios introducidos.
        r = np.linspace(self.dominio[0], self.dominio[1], 2)
        t = np.linspace(self.dominio[2], self.dominio[3], 50)
        p = np.linspace(self.dominio[4], self.dominio[5], 50)
        pw, tw = np.meshgrid(p, t)
        xw, yw = self.dominio[1]*np.cos(pw)*np.sin(tw), self.dominio[1]*np.sin(pw)*np.sin(tw)
        zw = self.dominio[1]*np.cos(tw)
        xw2, yw2 = self.dominio[1]*np.cos(p), self.dominio[1]*np.sin(p)
        canva.axes.set_xlim(xw.min(), xw.max())
        canva.axes.set_ylim(yw.min(), yw.max())
        canva.axes.set_zlim(zw.min(), zw.max())
        canva.axes.plot_surface(xw, yw, zw, lw = 0.5, color="black", alpha = 0.07)
        canva.axes.plot(xw2.T, yw2.T, zs=0, lw = 0.5, color="black", alpha = 0.3)

        return [longitud, resolucion]
    
    def crearProyeccion3D_esfericas(self, canva, coordenada):
        """
        Diseño de la proyección para problemas con tres dimensiones espaciales en coordenadas esféricas

        Parámetros
        ----------
        canva: Matplotlib.figure
            Figura de Matplotlib que contiene la gráfica.

        coordenada: string
            Coordenada fija de la solución.

        Salida
        ----------
        [abcisa, ordenada, coordenada_fija, longitud, resolucion]

            abcisa: lista flotantes
                Partición de la coordenada que funcionará como eje de abcisas.

            ordenada: lista flotantes
                Partición de la coordenada que funcionará como eje de ordenadas.

            coordenada_fija: string
                Coordenada fija.

            longitud: entero
                Longitud de la partición de la coordenada fija.

            resolucion: entero
                Resolucion temporal de la animación.
        """

        self.dominio = [float(self.Dominio[0][0]), float(self.Dominio[0][1]), float(self.Dominio[1][0]), float(self.Dominio[1][1]), float(self.Dominio[-1][0]), float(self.Dominio[-1][1])]
        self.Cota = max(abs(self.minimo-(self.maximo-self.minimo)*0.05), abs(self.maximo+(self.maximo-self.minimo)*0.05))
        resolucion = 25

        if coordenada == "r":
            # Diseño del lienzo.
            canva.axes = canva.figura.add_subplot(1, 2, 1, projection='polar')
            canva.axes.set_position([0.05, 0.35, 0.35, 0.35])
            canva.axes.set_facecolor((0.52, 0.50, 0.49, 0.3))
            canva.axes2 = canva.figura.add_subplot(1, 2, 2, projection='polar')
            canva.axes2.set_position([0.45, 0.35, 0.35, 0.35])
            canva.axes2.set_facecolor((0.52, 0.50, 0.49, 0.3))
            canva.axes.set_xlim(0, self.dominio[5])
            canva.axes.set_ylim(self.dominio[0], self.dominio[1])
            canva.axes2.set_xlim(0, self.dominio[5])
            canva.axes2.set_ylim(self.dominio[0], self.dominio[1])
            if self.dominio[5] <= np.pi/2:
                number = 5
            elif np.pi/2 < self.dominio[5] <= 3*np.pi/2:
                number = 7
            else:
                number = 9
            thetagrid = np.linspace(0, self.dominio[5]*180/np.pi, number)

            # Diseño de las etiquetas angulares de la gráfica 1.
            canva.axes.tick_params(labelsize=7)
            canva.axes.set_thetagrids(thetagrid if self.dominio[5] != 2*np.pi else thetagrid[:-1], fontsize=10)
            canva.axes.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(self.calculoEtiquetasRadianes))

            # Diseño de las etiquetas radiales de la gráfica 1.
            canva.axes.set_rlabel_position(25)
            canva.axes.set_yticks(np.arange(self.dominio[0], self.dominio[1]+(self.dominio[1]-self.dominio[0])/10, (self.dominio[1]-self.dominio[0])/5)[1:])
            canva.axes.grid(lw=0.2)

            # Diseño de las etiquetas angulares de la gráfica 2.
            canva.axes2.tick_params(labelsize=7)
            canva.axes2.set_thetagrids(thetagrid if self.dominio[5] != 2*np.pi else thetagrid[:-1], fontsize=10)
            canva.axes2.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(self.calculoEtiquetasRadianes))

            # Diseño de las etiquetas radiales de la gráfica 2.
            canva.axes2.set_rlabel_position(25)
            canva.axes2.set_yticks(np.arange(self.dominio[0], self.dominio[1]+(self.dominio[1]-self.dominio[0])/10, (self.dominio[1]-self.dominio[0])/5)[1:])
            canva.axes2.grid(lw=0.2)
        
            # Diseño de las leyendas.
            canva.axes.set_xlabel(r"$\bf{\phi}$")
            canva.axes2.set_xlabel(r"$\bf{\phi}$")

            # Variables de ayuda para la graficación y animación.
            # El procesamiento de los datos para la creación de una gráfica de proyección de r en coordenadas esféricas se basó en Wilson, R. (24 de febrero de 2012). Producing polar contour plots with matplotlib. Robin's blog. https://blog.rtwilson.com/producing-polar-contour-plots-with-matplotlib/
            self.x, self.y = self.Dominios[1], self.Dominios[2]
            abcisa = self.Dominios[1]
            ordenada = self.Dominios[2]
            longitud = len(self.Dominios[0])
        elif coordenada == "theta":
            # Diseño del lienzo.
            canva.axes = canva.figura.add_subplot(projection='polar')
            canva.axes.set_xlim(self.dominio[4], self.dominio[5])
            canva.axes.set_ylim(self.dominio[0], self.dominio[1])
            canva.axes.set_title(r'$\theta = %(valor)s$' % {"valor":self.dominio[2]} , pad = 10) 
            canva.axes.set_position([0.15, 0.2, 0.65, 0.65])
            canva.axes.set_facecolor((0.52, 0.50, 0.49, 0.3))
            # Determinación del número de puntos en los que se divide el eje angular.
            if self.dominio[3] <= np.pi/2:
                number = 5
            elif np.pi/2 < self.dominio[3] <= 3*np.pi/2:
                number = 7
            else:
                number = 9
            thetagrid = np.linspace(0, self.dominio[5]*180/np.pi, number)

            # Diseño de las etiquetas angulares.
            canva.axes.set_thetagrids(thetagrid if self.dominio[5] != 2*np.pi else thetagrid[:-1])
            canva.axes.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(self.calculoEtiquetasRadianes))

            # Diseño de las etiquetas radiales.
            canva.axes.set_rlabel_position(25)
            canva.axes.set_yticks(np.arange(self.dominio[0], self.dominio[1]+(self.dominio[1]-self.dominio[0])/10, (self.dominio[1]-self.dominio[0])/5)[1:])
            canva.axes.grid(lw=0.2)

            # Variables de ayuda para la graficación y animación.
            self.u, self.v = np.meshgrid(self.Dominios[0], self.Dominios[2])
            abcisa = self.Dominios[2]
            ordenada = self.Dominios[0]
            longitud = len(self.Dominios[1])
        elif coordenada == "phi":
            # Diseño del lienzo.
            canva.axes = canva.figura.add_subplot(projection='polar')
            canva.axes.set_xlim(self.dominio[2], self.dominio[3])
            canva.axes.set_ylim(self.dominio[0], self.dominio[1])

            # El cambio en la orientación de los ángulos (para que vayan en sentido contrario a las manecillas del reloj) fue tomado de Kumar Rishi, R. (06 de mayo de 2021). How to make the angles in a Matplotlib polar plot go clockwise with 0° at the top?. tutorialspoint. https://www.tutorialspoint.com/how-to-make-the-angles-in-a-matplotlib-polar-plot-go-clockwise-with-0-at-the-top
            canva.axes.set_theta_offset(np.pi)
            canva.axes.set_theta_direction(-1)

            canva.axes.set_title(r'$\phi = %(valor)s$' % {"valor":self.dominio[4]}, pad = 10) 
            canva.axes.set_position([0.15, 0.2, 0.65, 0.65])
            canva.axes.set_facecolor((0.52, 0.50, 0.49, 0.3))
            if self.dominio[5] <= np.pi/2:
                number = 5
            elif np.pi/2 < self.dominio[5] <= 3*np.pi/2:
                number = 7
            else:
                number = 9
            thetagrid = np.linspace(0, self.dominio[3]*180/np.pi, number)

            # Diseño de las etiquetas angulares.
            canva.axes.set_thetagrids(thetagrid if self.dominio[3] != 2*np.pi else thetagrid[:-1])
            canva.axes.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(self.calculoEtiquetasRadianes))

            # Diseño de las etiquetas radiales.
            canva.axes.set_rlabel_position(25)
            canva.axes.set_yticks(np.arange(self.dominio[0], self.dominio[1]+(self.dominio[1]-self.dominio[0])/10, (self.dominio[1]-self.dominio[0])/5)[1:])
            canva.axes.grid(lw=0.2)

            # Variables de ayuda para la graficación y animación.
            # El procesamiento de los datos para la creación de una gráfica de proyección de phi en coordenadas esféricas se basó en Wilson, R. (24 de febrero de 2012). Producing polar contour plots with matplotlib. Robin's blog. https://blog.rtwilson.com/producing-polar-contour-plots-with-matplotlib/
            self.u, self.v = np.meshgrid(self.Dominios[0], self.Dominios[1])
            abcisa = self.Dominios[1]
            ordenada = self.Dominios[0]
            longitud = len(self.Dominios[2])
        
        return [abcisa, ordenada, coordenada, longitud, resolucion]

    def guardarAnimacion(self):
        """
        Guarda en un archivo .mov (a 25 FPS cuando hay dependencia temporal o 10 FPS cuando no lo hay) una animación mostrando la solución para distintos tiempos o distintos valores de coordenada fija (en problemas con dependencia temporal o con tres dimensiones espaciales, respectivamente) o la creación de la gráfica (en problemas sin dependencia temporal y con dos dimensiones espaciales o en la proyección en problemas de una dimensión espacial).
        """

        self.Animacion.runs = False
        self.envioActualizacion("Iniciando Gráfica")
        
        # Preparación de la gráfica y los datos de guardado.
        if self.Proyeccion:
            # Para guardado con proyección.
            self.proyectado = True
            if (len(self.Dominio) == 2) and self.dependencia_tiempo:
                # Problemas de una dimensión espacial y dependencia temporal.
                self.DatosGrafica = self.crearProyeccion1D(self.MostrarSolucion2)
                argumentos = [*self.DatosGrafica, self.MatrizResultados, self.MostrarSolucion2.axes, self.Cota, self.Colormap, self.GuardarAnimacion]
                maximo = int(self.DatosGrafica[-2]*self.DatosGrafica[-1])+20-1
                minimo = 0
                funcion = self.introducirProyeccion1D
                nombre = "1DP_tiempo"
                resolucion = 25
            elif len(self.Dominios) == 2:
                # Para problemas con dos dimensiones espaciales.
                if self.Coordenadas == "Cartesianas":
                    self.DatosGrafica = self.crearProyeccion2D_cartesianas(self.MostrarSolucion2)
                    coordenadas = "cartesianas"
                elif self.Coordenadas == "Cilíndricas / Polares":
                    self.DatosGrafica = self.crearProyeccion2D_polares(self.MostrarSolucion2)
                    coordenadas = "cilindricas_polares"
                if self.dependencia_tiempo:
                    # Problemas con dependencia temporal.
                    argumentos = [int(len(self.DatosGrafica[0])/10), *self.DatosGrafica, self.Coordenadas, self.MatrizResultados, self.MostrarSolucion2.axes, self.Cota, self.Colormap, self.GuardarAnimacion]
                    maximo = int(len(self.DatosGrafica[0])/10+self.DatosGrafica[-2]*self.DatosGrafica[-1])+20
                    minimo = int(len(self.DatosGrafica[0])/10)
                    funcion = self.actualizarProyeccion2D
                    nombre = "2DP_tiempo_{}".format(coordenadas)
                    resolucion = 25
                else:
                    # Problemas sin dependencia temporal.
                    argumentos = [int(len(self.DatosGrafica[0])/10), *self.DatosGrafica[0:-2], self.Coordenadas, self.MatrizResultados, self.MostrarSolucion2.axes, self.Cota, self.Colormap, self.GuardarAnimacion]
                    maximo = int(len(self.DatosGrafica[0])/10)+20
                    minimo = 0
                    funcion = self.introducirProyeccion2D
                    nombre = "2DP_notiempo_{}".format(coordenadas)
                    resolucion = 10
            elif len(self.Dominios) == 3:
                # Para problemas con tres dimensiones espaciales.
                if self.CoordenadaFija_1.isChecked():
                    if self.Coordenadas == "Cartesianas":
                        coordenada_especifica = "x"
                    else:
                        coordenada_especifica = "r"
                    self.Valores = self.MatrizResultados.T.swapaxes(1, 2)
                    limites = self.dominio[0:2]
                elif self.CoordenadaFija_2.isChecked():
                    if self.Coordenadas == "Cartesianas":
                        coordenada_especifica = "y"
                    elif self.Coordenadas == "Cilíndricas / Polares":
                        coordenada_especifica = "phi"
                    elif self.Coordenadas == "Esféricas":
                        coordenada_especifica = "theta"
                    self.Valores = self.MatrizResultados.T.swapaxes(0, 1).swapaxes(1, 2)
                    limites = self.dominio[2:4]
                elif self.CoordenadaFija_3.isChecked():
                    if self.Coordenadas == "Esféricas":
                        coordenada_especifica = "phi"
                    else:
                        coordenada_especifica = "z"
                    self.Valores = self.MatrizResultados
                    limites = self.dominio[4:]

                if self.Coordenadas == "Cartesianas":
                    self.DatosGrafica = self.crearProyeccion3D_cartesianas(self.MostrarSolucion2, coordenada_especifica)
                    coordenadas = "cartesianas"
                elif self.Coordenadas == "Cilíndricas / Polares":
                    self.DatosGrafica = self.crearProyeccion3D_cilindricas(self.MostrarSolucion2, coordenada_especifica)
                    coordenadas = "cilindricas_polares"
                elif self.Coordenadas == "Esféricas":
                    self.DatosGrafica = self.crearProyeccion3D_esfericas(self.MostrarSolucion2, coordenada_especifica)
                    coordenadas = "esfericas"
        
                if (self.CoordenadaFija_1.isChecked()) and (self.Coordenadas == "Esféricas"):
                    # Problemas con coordenadas esféricas y el radio como coordenada fija.
                    argumentos = [int(len(self.DatosGrafica[1])/10), *self.DatosGrafica[0:2], *self.DatosGrafica[3:-1], self.Valores, limites, self.MostrarSolucion2.figura, self.Cota, self.Colormap, self.GuardarAnimacion]
                    maximo = int(len(self.DatosGrafica[1])/10+self.DatosGrafica[-2])+20
                    minimo = int(len(self.DatosGrafica[1])/10)
                    funcion = self.actualizarProyeccion3D_especial
                else:
                    # Cualquier otro problema.
                    argumentos = [int(len(self.DatosGrafica[0])/10), *self.DatosGrafica[0:2], *self.DatosGrafica[3:-1], self.Coordenadas, self.Valores, self.MostrarSolucion2.axes, coordenada_especifica, limites, self.Cota, self.Colormap, self.GuardarAnimacion]
                    maximo = int(len(self.DatosGrafica[0])/10+self.DatosGrafica[-2])+20
                    minimo = int(len(self.DatosGrafica[0])/10)
                    funcion = self.actualizarProyeccion3D

                nombre = "3DP_{}".format(coordenada_especifica)
                resolucion = 10
        else:
            # Para guardado sin proyección.
            self.proyectado = False
            if (len(self.Dominio) == 2) and (len(self.Dominio[-1]) == 1): 
                # Problemas con una dimensión espacial y depedencia temporal.
                self.DatosGrafica = self.crearGrafica1D(self.MostrarSolucion2)
                argumentos = [int(len(self.DatosGrafica[0])/10), *self.DatosGrafica, self.Segmentos, self.MatrizResultados, self.MostrarSolucion2.axes, None, None, self.Cota, self.Colormap, self.GuardarAnimacion] 
                maximo = int(len(self.DatosGrafica[0])/10+self.DatosGrafica[-2]*self.DatosGrafica[-1])+20
                minimo = int(len(self.DatosGrafica[0])/10)
                funcion = self.actualizarAnimacion1D
                nombre = "1D_tiempo"
                resolucion = 25
            elif len(self.Dominios) == 2:
                # Problemas con dos dimensiones espaciales.
                if self.Coordenadas == "Cartesianas":
                    self.DatosGrafica = self.crearGrafica2D_cartesianas(self.MostrarSolucion2)
                    coordenadas = "cartesianas"
                elif self.Coordenadas == "Cilíndricas / Polares":
                    self.DatosGrafica = self.crearGrafica2D_polares(self.MostrarSolucion2)
                    coordenadas = "cilindricas_polares"
                if self.dependencia_tiempo:
                    # Problemas con dependencia temporal.
                    argumentos = [int(len(self.DatosGrafica[0].T)/10), *self.DatosGrafica, self.Coordenadas, self.MatrizResultados, self.MostrarSolucion2.axes, self.ccount, self.rcount, self.Cota, self.Colormap, self.GuardarAnimacion]
                    maximo = int(len(self.DatosGrafica[0].T)/10+self.DatosGrafica[-2]*self.DatosGrafica[-1])+20
                    minimo = int(len(self.DatosGrafica[0].T)/10)
                    funcion = self.actualizarAnimacion2D
                    nombre = "2D_tiempo_{}".format(coordenadas)
                    resolucion = 25
                else:
                    # Problemas sin depedencia temporal.
                    argumentos = [int(len(self.DatosGrafica[0].T)/10), *self.DatosGrafica, self.Coordenadas, self.MatrizResultados, self.MostrarSolucion2.axes, self.ccount, self.rcount, self.Cota, self.Colormap, self.GuardarAnimacion]
                    maximo = int(len(self.DatosGrafica[0].T)/10)+20
                    minimo = 0
                    funcion = self.introducirGrafica2D
                    nombre = "2D_notiempo_{}".format(coordenadas)
                    resolucion = 10
            elif len(self.Dominios) == 3:
                # Problemas con tres dimensiones espaciales.
                if self.CoordenadaFija_1.isChecked():
                    if self.Coordenadas == "Cartesianas":
                        coordenada_especifica = "x"
                        longitud2 = int(len(self.Dominios[1])/10)
                    elif self.Coordenadas == "Cilíndricas / Polares":
                        coordenada_especifica = "r"
                        longitud2 = int(len(self.Dominios[2])/10)
                    elif self.Coordenadas == "Esféricas":
                        coordenada_especifica = "r"
                        longitud2 = int(len(self.Dominios[1])/10)
                    self.Valores = self.MatrizResultados.T.swapaxes(1, 2)
                    limites = self.dominio[0:2]
                elif self.CoordenadaFija_2.isChecked():
                    if self.Coordenadas == "Cartesianas":
                        coordenada_especifica = "y"
                    elif self.Coordenadas == "Cilíndricas / Polares":
                        coordenada_especifica = "phi"
                    elif self.Coordenadas == "Esféricas":
                        coordenada_especifica = "theta"
                    longitud2 = int(len(self.Dominios[0])/10)
                    self.Valores = self.MatrizResultados.T.swapaxes(0, 1).swapaxes(1, 2)
                    limites = self.dominio[2:4]
                elif self.CoordenadaFija_3.isChecked():
                    if self.Coordenadas == "Esféricas":
                        coordenada_especifica = "phi"
                    else:
                        coordenada_especifica = "z"
                    longitud2 = int(len(self.Dominios[0])/10)
                    self.Valores = self.MatrizResultados
                    limites = self.dominio[4:]
                        
                if self.Coordenadas == "Cartesianas":
                    self.DatosGrafica = self.crearGrafica3D_cartesianas(self.MostrarSolucion2, coordenada_especifica)
                    coordenadas = "cartesianas"
                elif self.Coordenadas == "Cilíndricas / Polares":
                    self.DatosGrafica = self.crearGrafica3D_cilindricas(self.MostrarSolucion2, coordenada_especifica)
                    coordenadas = "cilindricas_polares"
                elif self.Coordenadas == "Esféricas":
                    self.DatosGrafica = self.crearGrafica3D_esfericas(self.MostrarSolucion2, coordenada_especifica)
                    coordenadas = "esfericas"
                argumentos = [longitud2, *self.Dominios, self.x, self.y, self.DatosGrafica[0], self.Coordenadas, coordenada_especifica, plt.Normalize(vmin = -self.Cota, vmax = self.Cota), self.Valores, self.MostrarSolucion2.axes, limites, self.rcount, self.ccount, self.Cota, self.Colormap, self.GuardarAnimacion]
                maximo = int(longitud2+self.DatosGrafica[0]+20)
                minimo = int(longitud2)
                funcion = self.actualizarGrafica3D
                nombre = "3D_{}".format(coordenadas+"_"+coordenada_especifica)
                resolucion = 10

        self.envioActualizacion("Configurando Opciones")

        # Configuración de las curvas de nivel.
        if self.curvas:
            curvas_str = "_Curvas"
            self.funcion_curvas = self.interpretacionCurvasNivel
        else:
            curvas_str = ""
        
        # Configuración de la herramienta de guardado.
        self.animacion = GuardadoAnimacion(self.MostrarSolucion2, funcion, fargs = argumentos, maximo = maximo, interval = 1000/resolucion, curvas_nivel = self.curvas, funcion_curvas = self.funcion_curvas, numero_introduccion = minimo, proyeccion = self.proyectado)

        self.envioActualizacion("Guardando Cuadros")

        # Configuración de los datos de guardado.
        metadata = dict(title='SolucionEDP', artist='GraficadoraSLP')
        # La modificación del bitrate y dpi de la animación para optimizar el guardado se basan en DrV. (08 de agosto de 2014). Respuesta a la pregunta "matplotlib animation movie: quality of movie decreasing with time". stackoverflow. https://stackoverflow.com/a/25209973
        # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 3.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/3.0/
        writer = FFMpegFileWriter(fps=resolucion, metadata=metadata, bitrate = 12000)
        self.animacion.save("Solucion_{}.mov".format(nombre+curvas_str), writer=writer, dpi=72)

        # Finalización
        self.animacion.finalizar()
        
    def cambiarCoordenadaFija(self):
        """
        Cambia la coordenada fija para visualizar la solución en problemas con tres dimensiones.
        """

        # Eliminación de las gráficas visibles.
        self.MostrarSolucion.figura.clear()
        self.MostrarSolucion.figura.canvas.draw_idle()

        if not self.dependencia_tiempo:
            # Determinación de la coordenada fija deseada en problemas sin dependencia temporal.
            if self.CoordenadaFija_1.isChecked():
                if self.Coordenadas == "Cartesianas":
                    coordenada = "x"
                elif self.Coordenadas == "Cilíndricas / Polares" or self.Coordenadas == "Esféricas":
                    coordenada = "r"
            elif self.CoordenadaFija_2.isChecked():
                if self.Coordenadas == "Cartesianas":
                    coordenada = "y"
                elif self.Coordenadas == "Cilíndricas / Polares":
                    coordenada = "phi"
                elif self.Coordenadas == "Esféricas":
                    coordenada = "theta"
            elif self.CoordenadaFija_3.isChecked():
                if self.Coordenadas == "Cartesianas" or self.Coordenadas == "Cilíndricas / Polares":
                    coordenada = "z"
                elif self.Coordenadas == "Esféricas":
                    coordenada = "phi"

        if self.ProyeccionEntrada.isChecked():
            # Cuando se está visualizando la proyección.
            self.Proyeccion = True
        
            if self.CurvasNivelAuto.isChecked():
                # Cuando se tienen curvas de nivel calculadas automáticamente.
                self.graficacion(curvas_nivel = True, casilla = self.CurvasNivelAuto,coordenada_especifica=coordenada)   
            elif self.CurvasNivelEspecificas.isChecked():
                # Cuando se tienen curvas de nivel especificadas manualmente.
                self.graficacion(curvas_nivel = True, casilla = self.CurvasNivelEspecificas,coordenada_especifica=coordenada) 
            else:
                # Cuando no se visualizan curvas de nivel.
                self.graficacion(coordenada_especifica=coordenada)
        else:
            # Cuando se visualiza la gráfica sin proyección.
            self.Proyeccion = False

            if self.CurvasNivelAuto.isChecked():
                # Cuando se tienen curvas de nivel calculadas automáticamente.
                self.graficacion(curvas_nivel = True, casilla = self.CurvasNivelAuto,coordenada_especifica=coordenada)   
            elif self.CurvasNivelEspecificas.isChecked():
                # Cuando se tienen curvas de nivel especificadas manualmente.
                self.graficacion(curvas_nivel = True, casilla = self.CurvasNivelEspecificas,coordenada_especifica=coordenada) 
            else:
                # Cuando no se quieren visualizar curvas de nivel.
                self.graficacion(coordenada_especifica=coordenada)

    def cambiarValorCoordenadaFija(self):
        """
        Cambia el corte visualizado en problemas con tres dimensiones. Lee el valor introducido por el usuario, calcula todos los valores de la solución para ese valor especifico y muestra la gráfica correspondiente.
        """
    
        try:
            self.envioActualizacion("Interpretando Valor")

            if self.CoordenadaFija.text() == "":
                raise NoNumeroError
            else:
                valor_coordenadaFija = float(parsing.parse_expr(self.CoordenadaFija.text()))
                if self.dependencia_tiempo:
                    if  valor_coordenadaFija >= 0:
                        self.envioActualizacion("Calculando Solución")
                        if len(self.Dominio) == 2:
                            # Problema con una dimensión espacial y dependencia temporal.

                            # Calculo de la solución para el tiempo especificado.
                            self.ValoresSolucion = np.zeros(int(len(self.Dominios[0])))
                            for indice in range(len(self.Dominios[0])):
                                self.ValoresSolucion[indice] = self.Funcion(self.Dominios[0][indice], valor_coordenadaFija)
                            puntos = np.array([self.Dominios[0], self.ValoresSolucion]).T.reshape(-1, 1, 2)
                            segmentos = np.concatenate([puntos[:-1], puntos[1:]], axis=1)

                            self.envioActualizacion("Graficando Solución")

                            # Graficación de la solución.
                            self.DatosGrafica[1].set_segments(segmentos)
                            self.DatosGrafica[1].set_array(self.ValoresSolucion)
                            self.MostrarSolucion.axes.set_title(' Tiempo \n{:02d}:{:02d}.{:02d}'.format(int(valor_coordenadaFija//60), int(valor_coordenadaFija%60), int((valor_coordenadaFija*100)%100)), pad = -10)
                        else:
                            # Calculo de la solución para el tiempo especificado.
                            self.ValoresSolucion = np.zeros([int(len(self.Dominios[0])), int(len(self.Dominios[1]))])
                            for indice1 in range(len(self.Dominios[0])):
                                for indice2 in range(len(self.Dominios[1])):
                                    self.ValoresSolucion[indice1][indice2] = self.Funcion(self.Dominios[0][indice1], self.Dominios[1][indice2], valor_coordenadaFija)

                            self.envioActualizacion("Graficando Solución")

                            if self.Proyeccion:
                                # Para graficar proyecciones.
                                # Eliminación de las proyecciones visibles.
                                self.MostrarSolucion.axes.proyeccion.remove()
                                if self.Coordenadas == "Cartesianas":
                                    self.MostrarSolucion.axes.proyeccion = self.MostrarSolucion.axes.pcolormesh(self.x, self.y, self.ValoresSolucion, cmap = self.Colormap, vmin=-self.Cota, vmax=self.Cota)
                                elif self.Coordenadas == "Cilíndricas / Polares":
                                    self.MostrarSolucion.axes.proyeccion = self.MostrarSolucion.axes.pcolormesh(self.v, self.u, self.ValoresSolucion.T, cmap = self.Colormap, vmin=-self.Cota, vmax=self.Cota)
                                self.MostrarSolucion.axes.set_title(' Tiempo \n{:02d}:{:02d}.{:02d}'.format(int(valor_coordenadaFija//60), int(valor_coordenadaFija%60), int((valor_coordenadaFija*100)%100)), pad = -10)
                            else:
                                # Para graficas sin proyección.
                                # Eliminación de superficies visibles.
                                self.MostrarSolucion.axes.superficie.remove()
                                if self.Coordenadas == "Cartesianas":
                                    self.MostrarSolucion.axes.superficie = self.MostrarSolucion.axes.plot_surface(self.x, self.y, self.ValoresSolucion, cmap = self.Colormap, vmin=-self.Cota, vmax=self.Cota, ccount = self.ccount, rcount = self.rcount)
                                elif self.Coordenadas == "Cilíndricas / Polares":
                                    self.MostrarSolucion.axes.superficie = self.MostrarSolucion.axes.plot_surface(self.x, self.y, self.ValoresSolucion.T, cmap = self.Colormap, vmin=-self.Cota, vmax=self.Cota)
                                self.MostrarSolucion.axes.set_title(' Tiempo \n{:02d}:{:02d}.{:02d}'.format(int(valor_coordenadaFija//60), int(valor_coordenadaFija%60), int((valor_coordenadaFija*100)%100)), pad = -10)
                    else:
                        raise ValorFueraDominioError
                else:
                    if self.CoordenadaFija_1.isChecked():
                        if (valor_coordenadaFija <= self.dominio[1]) and (valor_coordenadaFija >= self.dominio[0]):
                            self.envioActualizacion("Calculando Solución")

                            # Calculo de la solución para el corte deseado.
                            self.ValoresSolucion = np.zeros([int(len(self.Dominios[1])), int(len(self.Dominios[2]))])
                            for indice1 in range(len(self.Dominios[1])):
                                for indice2 in range(0, len(self.Dominios[2])):
                                    self.ValoresSolucion[indice1][indice2] = self.Funcion(valor_coordenadaFija, self.Dominios[1][indice1], self.Dominios[2][indice2])

                            self.envioActualizacion("Graficando Solución")
                                
                            if self.Proyeccion:
                                # Para gráficas con proyección.
                                # Eliminación de la proyección visible.
                                self.MostrarSolucion.axes.proyeccion.remove()
                                if self.Coordenadas == "Cartesianas":
                                    self.MostrarSolucion.axes.proyeccion = self.MostrarSolucion.axes.pcolormesh(self.x, self.y, self.ValoresSolucion.T, cmap=self.Colormap, vmin=-self.Cota, vmax=self.Cota)
                                    coordenada = "x"
                                elif self.Coordenadas == "Cilíndricas / Polares":
                                    self.MostrarSolucion.axes.proyeccion = self.MostrarSolucion.axes.pcolormesh(self.x, self.y, self.ValoresSolucion.T, cmap=self.Colormap, vmin=-self.Cota, vmax=self.Cota)
                                    coordenada = "r"
                                elif self.Coordenadas == "Esféricas":
                                    self.MostrarSolucion.axes2.proyeccion.remove()
                                    r = np.linspace(0, valor_coordenadaFija, int(np.ceil(len(self.x)/2)))
                                    r1, phi1 = np.meshgrid(r, self.y)
                                    self.MostrarSolucion.axes.proyeccion = self.MostrarSolucion.axes.pcolormesh(phi1, r1, self.ValoresSolucion[:int(np.ceil(len(self.x)/2))].T, cmap=self.Colormap, vmin=-self.Cota, vmax=self.Cota)
                                    self.MostrarSolucion.axes2.proyeccion = self.MostrarSolucion.axes2.pcolormesh(phi1, r1, np.flip(self.ValoresSolucion[int(np.floor(len(self.x)/2)):].T,1), cmap=self.Colormap, vmin=-self.Cota, vmax=self.Cota)
                                    coordenada = "r"
                            else:
                                # Para gráficas sin proyección.
                                # Creación de la norma para colorear la solución.
                                norma = plt.Normalize(vmin = -self.Cota, vmax = self.Cota)
                                # Eliminación de superficies visibles.
                                self.MostrarSolucion.axes.superficie.remove()
                                if self.Coordenadas == "Cartesianas":
                                    self.MostrarSolucion.axes.superficie = self.MostrarSolucion.axes.plot_surface(valor_coordenadaFija, self.x, self.y, facecolors = self.Colormap(norma(self.ValoresSolucion.T)), shade=False)
                                    coordenada = "x"
                                elif self.Coordenadas == "Cilíndricas / Polares":
                                    x, y = valor_coordenadaFija*np.cos(self.x), valor_coordenadaFija*np.sin(self.x)
                                    self.MostrarSolucion.axes.superficie = self.MostrarSolucion.axes.plot_surface(x, y, self.y, facecolors = self.Colormap(norma(self.ValoresSolucion.T)), shade=False)
                                    coordenada = "r"
                                elif self.Coordenadas == "Esféricas":
                                    x, y = valor_coordenadaFija*np.cos(self.y)*np.sin(self.x), valor_coordenadaFija*np.sin(self.y)*np.sin(self.x)
                                    z = valor_coordenadaFija*np.cos(self.x)
                                    self.MostrarSolucion.axes.superficie = self.MostrarSolucion.axes.plot_surface(x, y, z, facecolors = self.Colormap(norma(self.ValoresSolucion.T)), shade=False)
                                    coordenada = "r"
                            self.MostrarSolucion.axes.set_title(r'${%(coordenada)s} = {%(valor)s}$' % {'coordenada': coordenada, 'valor': latex(parsing.parse_expr(self.CoordenadaFija.text()))}, pad = 10)        
                        else: 
                            raise ValorFueraDominioError
                    elif self.CoordenadaFija_2.isChecked():
                        if (valor_coordenadaFija <= self.dominio[3]) and (valor_coordenadaFija >= self.dominio[2]):
                            self.envioActualizacion("Calculando Solución")

                            # Calculo de la solución para el valor especificado.
                            self.ValoresSolucion = np.zeros([int(len(self.Dominios[0])), int(len(self.Dominios[2]))])
                            for indice1 in range(len(self.Dominios[0])):
                                for indice2 in range(0, len(self.Dominios[2])):
                                    self.ValoresSolucion[indice1][indice2] = self.Funcion(self.Dominios[0][indice1], valor_coordenadaFija, self.Dominios[2][indice2])

                            self.envioActualizacion("Graficando Solución")

                            if self.Proyeccion:
                                # Para gráficas con proyección.
                                # Eliminación de la proyección visible.
                                self.MostrarSolucion.axes.proyeccion.remove()
                                if self.Coordenadas == "Cartesianas":
                                    self.MostrarSolucion.axes.proyeccion = self.MostrarSolucion.axes.pcolormesh(self.x, self.y, self.ValoresSolucion.T, cmap=self.Colormap, vmin=-self.Cota, vmax=self.Cota)
                                    coordenada = "y"
                                elif self.Coordenadas == "Cilíndricas / Polares":
                                    self.MostrarSolucion.axes.proyeccion = self.MostrarSolucion.axes.pcolormesh(self.x, self.y, self.ValoresSolucion.T, cmap=self.Colormap, vmin=-self.Cota, vmax=self.Cota)
                                    coordenada = "\\phi"
                                elif self.Coordenadas == "Esféricas":
                                    self.MostrarSolucion.axes.proyeccion = self.MostrarSolucion.axes.pcolormesh(self.v, self.u*np.sin(valor_coordenadaFija), self.ValoresSolucion.T, cmap=self.Colormap, vmin=-self.Cota, vmax=self.Cota)
                                    coordenada = "\\theta"
                            else:
                                # Para gráficas sin proyección.
                                # Creación de la norma para colorear la solución.
                                norma = plt.Normalize(vmin = -self.Cota, vmax = self.Cota)
                                # Eliminación de superficies visibles.
                                self.MostrarSolucion.axes.superficie.remove()
                                if self.Coordenadas == "Cartesianas":
                                    self.MostrarSolucion.axes.superficie = self.MostrarSolucion.axes.plot_surface(self.x, valor_coordenadaFija, self.y, facecolors = self.Colormap(norma(self.ValoresSolucion.T)), shade=False)
                                    coordenada = "y"
                                elif self.Coordenadas == "Cilíndricas / Polares":
                                    x, y = self.x*np.cos(valor_coordenadaFija), self.x*np.sin(valor_coordenadaFija)
                                    self.MostrarSolucion.axes.superficie = self.MostrarSolucion.axes.plot_surface(x, y, self.y, facecolors = self.Colormap(norma(self.ValoresSolucion.T)), shade=False)
                                    coordenada = "\\phi"
                                elif self.Coordenadas == "Esféricas":
                                    x, y = self.x*np.cos(self.y)*np.sin(valor_coordenadaFija), self.x*np.sin(self.y)*np.sin(valor_coordenadaFija)
                                    z = self.x*np.cos(valor_coordenadaFija)
                                    self.MostrarSolucion.axes.superficie = self.MostrarSolucion.axes.plot_surface(x, y, z, facecolors = self.Colormap(norma(self.ValoresSolucion.T)), shade=False)
                                    coordenada = "\\theta"
                            self.MostrarSolucion.axes.set_title(r'${%(coordenada)s} = {%(valor)s}$' % {'coordenada': coordenada, 'valor': latex(parsing.parse_expr(self.CoordenadaFija.text()))}, pad = 10)  
                        else: 
                            raise ValorFueraDominioError
                    elif self.CoordenadaFija_3.isChecked():
                        if (valor_coordenadaFija <= self.dominio[5]) and (valor_coordenadaFija >= self.dominio[4]):
                            self.envioActualizacion("Calculando Solución")
    
                            # Calculo de la solución para el valor especificado.
                            self.ValoresSolucion = np.zeros([int(len(self.Dominios[0])), int(len(self.Dominios[1]))])
                            for indice1 in range(len(self.Dominios[0])):
                                for indice2 in range(len(self.Dominios[1])):
                                    self.ValoresSolucion[indice1][indice2] = self.Funcion(self.Dominios[0][indice1], self.Dominios[1][indice2], valor_coordenadaFija)

                            self.envioActualizacion("Graficando Solución")

                            if self.Proyeccion:
                                # Para gráficas con proyección.
                                # Eliminación de la proyección visible.
                                self.MostrarSolucion.axes.proyeccion.remove()
                                if self.CoordenadaFija_3.isChecked():
                                    if self.Coordenadas == "Cartesianas":
                                        self.MostrarSolucion.axes.proyeccion = self.MostrarSolucion.axes.pcolormesh(self.x, self.y.T, self.ValoresSolucion.T, cmap=self.Colormap, vmin=-self.Cota, vmax=self.Cota)
                                        coordenada = "y"
                                    elif self.Coordenadas == "Cilíndricas / Polares":
                                        self.MostrarSolucion.axes.proyeccion = self.MostrarSolucion.axes.pcolormesh(self.DatosGrafica[0], self.DatosGrafica[1], self.ValoresSolucion, cmap=self.Colormap, vmin=-self.Cota, vmax=self.Cota)
                                        coordenada = "z"
                                    elif self.Coordenadas == "Esféricas":
                                        self.MostrarSolucion.axes.proyeccion = self.MostrarSolucion.axes.pcolormesh(self.DatosGrafica[0], self.DatosGrafica[1], self.ValoresSolucion, cmap=self.Colormap, vmin=-self.Cota, vmax=self.Cota)
                                        coordenada = "\\phi"
                            else:
                                # Para gráficas sin proyección.
                                # Creación de la norma para colorear la solución.
                                norma = plt.Normalize(vmin = -self.Cota, vmax = self.Cota)
                                # Eliminación de superficies visibles.
                                self.MostrarSolucion.axes.superficie.remove()
                                if self.Coordenadas == "Cartesianas":
                                    self.MostrarSolucion.axes.superficie = self.MostrarSolucion.axes.plot_surface(self.x, self.y, valor_coordenadaFija*(1+(self.x**2+self.y**2)*0), facecolors = self.Colormap(norma(self.ValoresSolucion.T)), shade=False)
                                    coordenada = "z"
                                elif self.Coordenadas == "Cilíndricas / Polares":
                                    self.MostrarSolucion.axes.superficie = self.MostrarSolucion.axes.plot_surface(self.x, self.y, valor_coordenadaFija*(1+(self.x**2+self.y**2)*0), facecolors = self.Colormap(norma(self.ValoresSolucion.T)), shade=False)
                                    coordenada = "z"
                                elif self.Coordenadas == "Esféricas":
                                    x, y = self.x*np.cos(valor_coordenadaFija)*np.sin(self.y), self.x*np.sin(valor_coordenadaFija)*np.sin(self.y)
                                    z = self.x*np.cos(self.y)
                                    self.MostrarSolucion.axes.superficie = self.MostrarSolucion.axes.plot_surface(x, y, z, facecolors = self.Colormap(norma(self.ValoresSolucion.T)), shade=False)
                                    coordenada = "\\phi"
                            self.MostrarSolucion.axes.set_title(r'${%(coordenada)s} = {%(valor)s}$' % {'coordenada': coordenada, 'valor': latex(parsing.parse_expr(self.CoordenadaFija.text()))}, pad = 10)  

                        else: 
                            raise ValorFueraDominioError

                self.valorespecial = True

                if not ((len(self.Dominio) == 3) and (not self.ProyeccionEntrada.isChecked()) and (not self.dependencia_tiempo)):
                    # Graficación de curvas de nivel en los problemas aceptados.

                    self.envioActualizacion("Añadiendo Curvas de Nivel")

                    if self.CoordenadaFija_3.isChecked():
                        if self.CurvasNivelAuto.isChecked() or self.CurvasNivelEspecificas.isChecked():
                            self.interpretacionCurvasNivel(coordenada_fija = True, valores_matriz = self.ValoresSolucion)
                    else:
                        if self.CurvasNivelAuto.isChecked() or self.CurvasNivelEspecificas.isChecked():
                            self.interpretacionCurvasNivel(coordenada_fija = True, valores_matriz = self.ValoresSolucion.T)
        except:
            tipoError, explicacion, line = sys.exc_info()[:3]

            print(tipoError, explicacion, line)

            if tipoError == NoNumeroError:
                raise NoNumeroError
            elif tipoError == ValorFueraDominioError:
                raise ValorFueraDominioError
            else:
                raise Exception

    def intercambiarProyeccion(self):
        """Intercambia entre proyección y gráfica."""

        self.envioActualizacion("Cambiando Proyección")
        self.curvasdibujadas = False
        self.valorespecial = False
        # Eliminación de la gráfica visible.
        self.MostrarSolucion.figura.clear()
        self.MostrarSolucion.figura.canvas.draw_idle()

        coordenada = None
        # Determinación de la coordenada fija para problemas de tres dimensiones espaciales.
        if len(self.dominio) == 6:
            if self.CoordenadaFija_1.isChecked():
                if self.Coordenadas == "Cartesianas":
                    coordenada = "x"
                elif self.Coordenadas == "Cilíndricas / Polares" or self.Coordenadas == "Esféricas":
                    coordenada = "r"
            elif self.CoordenadaFija_2.isChecked():
                if self.Coordenadas == "Cartesianas":
                    coordenada = "y"
                elif self.Coordenadas == "Cilíndricas / Polares":
                    coordenada = "phi"
                elif self.Coordenadas == "Esféricas":
                    coordenada = "theta"
            elif self.CoordenadaFija_3.isChecked():
                if self.Coordenadas == "Cartesianas" or self.Coordenadas == "Cilíndricas / Polares":
                    coordenada = "z"
                elif self.Coordenadas == "Esféricas":
                    coordenada = "phi"

        self.envioActualizacion("Graficando")

        if self.ProyeccionEntrada.isChecked():
            self.Proyeccion = True
            # Creación de la proyección.
            if not ((len(self.Dominio) == 2) and self.dependencia_tiempo):
                # Habilitación de las herramientas de curvas de nivel.
                self.CurvasNivelAuto.setCheckable(True)
                self.CurvasNivelEspecificas.setCheckable(True)
                self.GraficarCurvasFija.setStyleSheet(u"color: rgba(246, 247, 247, 255); background-color: rgb(11, 61, 98)")
                self.GraficarCurvasFija.setEnabled(True)
            else:
                # Deshabilitación de las herramientas de curvas de nivel y de corte.
                self.CoordenadaFija_1.setCheckable(False)
                self.CoordenadaFija_1.setEnabled(False)
                self.CurvasNivelAuto.setEnabled(False)
                self.CurvasNivelAuto.setCheckable(False)
                self.CurvasNivelEspecificas.setEnabled(False)
                self.CurvasNivelEspecificas.setCheckable(False)
                self.GraficarCurvasFija.setEnabled(False)
                self.GraficarCurvasFija.setStyleSheet("background-color: rgb(127,146,151); color: rgb(234,237,239);")
                self.CoordenadaFija.setDisabled(True)
                self.GraficarCoordenadaFija.setEnabled(False)
                self.GraficarCoordenadaFija.setStyleSheet("background-color: rgb(127,146,151); color: rgb(234,237,239);")
            
            if self.CurvasNivelAuto.isChecked():
                # Graficación con curvas de nivel calculadas automáticamente.
                self.graficacion(curvas_nivel = True, casilla = self.CurvasNivelAuto,coordenada_especifica=coordenada)   
            elif self.CurvasNivelEspecificas.isChecked():
                # Graficación con curvas de nivel especificadas manualmente.
                self.graficacion(curvas_nivel = True, casilla = self.CurvasNivelEspecificas,coordenada_especifica=coordenada) 
            else:
                # Graficación sin curvas de nivel.
                self.graficacion(coordenada_especifica=coordenada)
        else:
            self.Proyeccion = False

            if (len(self.Dominio) == 2) and self.dependencia_tiempo:
                # Habilitación de las herramientas de corte.
                self.CoordenadaFija_1.setCheckable(True)
                self.CoordenadaFija_1.setChecked(True)
                self.CoordenadaFija_1.setEnabled(True)
            self.CoordenadaFija.setEnabled(True)
            self.GraficarCoordenadaFija.setEnabled(True)
            self.GraficarCoordenadaFija.setStyleSheet(u"color: rgba(246, 247, 247, 255); background-color: rgb(11, 61, 98)")

            # Creación de la gráfica.
            if (len(self.Dominio) == 3 and self.dependencia_tiempo) or (len(self.Dominios) == 2 and not self.dependencia_tiempo):
                if self.CurvasNivelAuto.isChecked():
                    # Graficación con curvas de nivel calculadas automáticamente.
                    self.graficacion(curvas_nivel = True, casilla = self.CurvasNivelAuto,coordenada_especifica=coordenada)   
                elif self.CurvasNivelEspecificas.isChecked():
                    # Graficación con curvas de nivel especificadas manualmente.
                    self.graficacion(curvas_nivel = True, casilla = self.CurvasNivelEspecificas,coordenada_especifica=coordenada) 
                else:
                    # Graficación sin curvas de nivel.
                    self.graficacion(coordenada_especifica=coordenada)
            else:
                # Graficación para problemas de tres dimensiones espaciales o con una dimension espacial y dependencia temporal.
                # Deshabilitación de las herramientas de curvas de nivel.
                self.CurvasNivelAuto.setCheckable(False)
                self.CurvasNivelEspecificas.setCheckable(False)
                self.graficacion(coordenada_especifica=coordenada)
    
    def interpretacionCurvasNivel(self, coordenada_fija = False, valores_matriz = None, guardar = False):
        """
        Interpreta la entrada del usuario para graficar o eliminar las curvas de nivel. En su caso, empieza el proceso de graficación de las curvas de nivel.
        
        Parámetros
        ----------
        coordenada_fija: bool
            Determina si hay una coordenada fija en la visualización.
        
        valores_matriz: arreglo de flotantes
            Valores especificos de la solución para graficar y calcular las curvas de nivel correspondientes.

        guardar: bool
            Determina si la aplicación está guardando una animación.
        """

        # Determinación del lienzo a utilizar.
        if guardar:
            canva = self.MostrarSolucion2
        else:
            canva = self.MostrarSolucion

        if self.valorespecial:
            coordenada_fija = True
        
        if self.CurvasNivelAuto.isChecked():
            self.curvas = True
            if self.carga:
                # Envio de actualización cuando no se está guardando la animación.
                self.envioActualizacion("Calculando Valores")

            # Calculo de los valores constantes con los que se buscarán las curvas de nivel.
            self.curvas_nivel = np.round(np.linspace(self.minimo+(self.maximo-self.minimo)/10, self.minimo+9*(self.maximo-self.minimo)/10, 9), self.Precision)

            if self.Animacion.curvas_nivel == False:
                # Configuración de los atributos de la animación para habilitar la visualización de curvas de nivel.
                self.Animacion.curvas_nivel = True
                self.Animacion.curvas_nivelcheck = self.CurvasNivelAuto
                self.Animacion.funcion_curvas = self.interpretacionCurvasNivel
            else:
                self.Animacion.curvas_nivelcheck = self.CurvasNivelAuto

            if self.carga:
                # Envio de actualización cuando no se está guardando la animación.
                self.envioActualizacion("Iniciando Graficación")

            if coordenada_fija == False:
                self.graficarCurvasNivel(valores = self.Valores, guardado = guardar)
            else:
                if self.valorespecial:
                    # Cuando se quiere graficar las curvas de nivel de la solución para un valor especifico para la coordenada fija.
                    self.graficarCurvasNivel(valores = self.ValoresSolucion, guardado = guardar)
                else:
                    # Cuando se quiere visualizar las curvas de nivel de la solución para los "valores predeterminados" (los valores calculados) de la coordenada fija.
                    self.graficarCurvasNivel(valores = valores_matriz, guardado = guardar)
        elif (self.CurvasNivelEspecificasEntrada.text() != "") and self.CurvasNivelEspecificas.isChecked():
            self.curvas = True
            if self.carga:
                # Envio de actualización cuando no se está guardando la animación.
                self.envioActualizacion("Interpretando Valores")

            # Interpretación de los valores introducidos por el usuario. La lista contiene el valor 100000 para superar la limitación de la función contour de requerir dos valores para lograr la graficación y así permitir la visualización de una sola curva de nivel.
            self.curvas_nivel = []
            for valor in self.CurvasNivelEspecificasEntrada.text().split(";"):
                if valor != "":
                    self.curvas_nivel.append(np.round(float(parsing.parse_expr(valor)), self.Precision))
            self.curvas_nivel.append(1000)

            if self.carga:
                # Envio de actualización cuando no se está guardando la animación.
                self.envioActualizacion("Iniciando Graficación")

            if self.Animacion.curvas_nivel == False:
                # Configuración de los atributos de la animación para habilitar la visualización de curvas de nivel.
                self.Animacion.curvas_nivel = True
                self.Animacion.curvas_nivelcheck = self.CurvasNivelEspecificas
                self.Animacion.funcion_curvas = self.interpretacionCurvasNivel
            else:
                self.Animacion.curvas_nivelcheck = self.CurvasNivelEspecificas
            
            if len(self.curvas_nivel) >= 2:
                # Graficación de las curvas de nivel especificadas solo cuando se establecen dos o más valores, puesto que en caso contrario la librería manda un error.
                if self.valorespecial:
                    # Cuando se quiere graficar las curvas de nivel de la solución para un valor especifico para la coordenada fija.
                    self.graficarCurvasNivel(valores = self.Valores, guardado = guardar)
                else:
                    # Cuando se quiere visualizar las curvas de nivel de la solución para los "valores predeterminados" (los valores calculados) de la coordenada fija.
                    self.graficarCurvasNivel(valores = valores_matriz, guardado = guardar)
                self.VentanaEtiquetas.show()
            else:
                self.VentanaEtiquetas.setHidden(True)
        else:
            self.curvas = False
            if self.carga:
                # Envio de actualización cuando no se está guardando la animación.
                self.envioActualizacion("Eliminando Curvas de Nivel")
 
            # Eliminación de las curvas de nivel dibujadas.
            if self.curvasdibujadas:
                for linea in self.Curvas.collections:
                    linea.remove()
                if len(canva.figura.axes) > 8:
                    if self.curvasdibujadas2:
                        for linea in self.Curvas2.collections:
                            linea.remove()
                self.curvasdibujadas = False
            # Cambio de opacidad de la solución para mostrar su color original.
            canva.axes.grid(True)
            if self.Proyeccion:
                canva.axes.proyeccion.set_alpha(1)
                if len(canva.figura.axes) > 8:
                    canva.axes2.proyeccion.set_alpha(1)
                    canva.axes2.grid(True)
            else:
                canva.axes.superficie.set_alpha(1)
            
            # Actualización del lienzo.
            canva.figura.canvas.draw_idle()

    def valorColor(self, valor):
        """Regresa el indice para determinar el color de acuerdo al valor de la solución."""

        # La definición de esta función se basa en cphlewis. (26 de febrero de 2015). Respuesta a la pregunta "Map values to colors in matplotlib". stackoverflow. https://stackoverflow.com/a/28753728
        # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 3.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/3.0/

        return (valor+self.Cota)/(2*self.Cota)      

    def graficarCurvasNivel(self, valores = None, guardado = False):
        """
        Grafica las curvas de nivel de acuerdo a los valores introducidos o calculados automáticamente por la función interpretacionCurvasNivel.
        
        Parámetros
        ----------
        valores: arreglo de flotantes
            Valores de la solución a utilizar para la graficación.
        
        guardado: bool
            Determina si se está guardando la animación.
        """
        # La creación de curvas de nivel en coordenadas polares, cilíndricas o esféricas (estas últimas en la proyección) se basó en Kington, J. (21 de enero de 2012). Respuesta a la pregunta "How to create a polar contour plot". stackoverflow. https://stackoverflow.com/a/9083017
        # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 3.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/3.0/

        if self.CurvasNivelAuto.isChecked() or self.CurvasNivelEspecificas.isChecked():
            # Determinación 
            if guardado:
                anim = self.animacion
                canva = self.MostrarSolucion2
            else:
                anim = self.Animacion
                canva = self.MostrarSolucion

            if self.carga:
                # Envio de actualización cuando no se está guardando la animación.
                self.envioActualizacion("Eliminando Curvas Anteriores")

            # Eliminación de las curvas de nivel dibujadas.
            if self.curvasdibujadas:
                for linea in self.Curvas.collections:
                    linea.remove()
                if len(canva.figura.axes) > 8:
                    if self.curvasdibujadas2:
                        for linea in self.Curvas2.collections:
                            linea.remove()
                if not guardado:
                    self.MostrarSolucion.figura.canvas.draw_idle()
            
            if self.carga:
                # Envio de actualización cuando no se está guardando la animación.
                self.envioActualizacion("Asignando Colores")
            
            # Interpretación de los valores para la creación de la leyenda. 
            self.curvas_nivel = sorted(self.curvas_nivel)
            self.curvas_nivel.reverse()
            curvas_etiquetas = ["z={}".format(valor) for valor in self.curvas_nivel]
            # La siguiente línea de código está basada en matplolib. (s. f.). Composing Custom Legends. matplolib.org. https://matplotlib.org/stable/gallery/text_labels_and_annotations/custom_legends.html
            curvas_especificas = [Line2D([0], [0], color=self.Colormap(self.valorColor(valor)), lw=2) for valor in self.curvas_nivel]
            self.curvas_nivel.reverse()

            try:
                self.curvasdibujadas = True
                if self.carga:
                    # Envio de actualización cuando no se está guardando la animación.
                    self.envioActualizacion("Graficando Curvas")

                if not ((len(self.Dominio) == 3) and (not self.Proyeccion)) and not self.dependencia_tiempo:
                    # Graficación de curvas de nivel para problemas que no sean de tres dimensiones espaciales.
                    if not self.valorespecial:
                        # Graficación de curvas de nivel cuando no se especifica un valor especifico para la coordenada fija (si es que se tiene una).
                        if self.Proyeccion:
                            canva.axes.proyeccion.set_alpha(0.4)
                            if (len(self.Dominios) == 2) and (not self.dependencia_tiempo):
                                # Curvas de nivel para problemas de dos dimensiones espaciales sin dependencia temporal.
                                self.Curvas = canva.axes.contour(self.x, self.y, self.MatrizResultados, levels=self.curvas_nivel, linewidths=3, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 2, alpha = 1)
                            elif len(canva.figura.axes) > 8:
                                # Curvas de nivel para proyección en coordenadas esféricas con radio como coordenada fija.
                                canva.axes2.proyeccion.set_alpha(0.4)
                                r = np.linspace(0, np.round((self.dominio[1]-self.dominio[0])*anim.deslizador.val/(len(self.Dominios[0])-1)+self.dominio[0], 2), int(np.ceil(len(self.x)/2)))
                                r1, phi1 = np.meshgrid(r, self.y)
                                self.Curvas = canva.axes.contour(phi1, r1, self.Valores[anim.deslizador.val].T[:int(np.ceil(len(self.x)/2))].T, levels=self.curvas_nivel, linewidths=3, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 2, alpha = 1)
                                self.Curvas2 = canva.axes2.contour(phi1, r1, np.flip(self.Valores[anim.deslizador.val].T[int(np.floor(len(self.x)/2)):].T, 1), levels=self.curvas_nivel, linewidths=3, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 2, alpha = 1)
                                self.curvasdibujadas2 = True
                                canva.axes2.grid(True)
                            elif self.Coordenadas == "Esféricas" and self.CoordenadaFija_2.isChecked():
                                # Curvas de nivel para proyección en coordenadas esféricas con el radio polar como coordenada fija.
                                self.Curvas = canva.axes.contour(self.v, self.u*np.sin(np.round((self.dominio[3]-self.dominio[2])*anim.deslizador.val/(len(self.Dominios[1])-1)+self.dominio[2], 2)), self.Valores[anim.deslizador.val], levels=self.curvas_nivel, linewidths=3, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 2, alpha = 1)
                            else:
                                self.Curvas = canva.axes.contour(self.v, self.u, self.Valores[anim.deslizador.val], levels=self.curvas_nivel, linewidths=3, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 2, alpha = 1)
                            canva.axes.grid(True)
                        else:
                            # Curvas de nivel para gráficas sin proyección.
                            canva.axes.superficie.set_alpha(0.4)
                            self.Curvas = canva.axes.contour(self.x, self.y, self.MatrizResultados, levels=self.curvas_nivel, linewidths=2, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 1, alpha = 1)
                            canva.axes.grid(True)
                    else:
                        # Graficación de curvas de nivel cuando se especifica un valor especifico para la coordenada fija (si es que se tiene una).
                        if self.Proyeccion and (len(canva.figura.axes) < 8):
                            # Curvas de nivel para visualizaciones de proyecciones que no correspondan a coordenadas esféricas con radio como coordenada fija.
                            canva.axes.proyeccion.set_alpha(0.4)
                            self.Curvas = canva.axes.contour(self.x, self.y, valores[anim.deslizador.val], levels=self.curvas_nivel, linewidths=3, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 2, alpha = 1)
                        elif len(canva.figura.axes) > 8:
                            # Curvas de nivel para visualizaciones de proyecciones en coordenadas esféricas con radio como coordenada fija.
                            canva.axes.proyeccion.set_alpha(0.4)
                            canva.axes2.proyeccion.set_alpha(0.4)
                            r = np.linspace(0, np.round((self.dominio[1]-self.dominio[0])*anim.deslizador.val/(len(self.Dominios[0])-1)+self.dominio[0], 2), int(np.ceil(len(self.x)/2)))
                            r1, phi1 = np.meshgrid(r, self.y)
                            self.Curvas = canva.axes.contour(phi1, r1, valores[anim.deslizador.val].T[:int(np.ceil(len(self.x)/2))].T, levels=self.curvas_nivel, linewidths=3, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 2, alpha = 1)
                            self.Curvas2 = canva.axes2.contour(phi1, r1, np.flip(valores[anim.deslizador.val].T[int(np.floor(len(self.x)/2)):].T,1), levels=self.curvas_nivel, linewidths=3, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 2, alpha = 1)
                            self.curvasdibujadas2 = True
                            canva.axes2.grid(True)
                        else:
                            # Curvas de nivel para graficas sin proyección.
                            canva.axes.superficie.set_alpha(0.4)
                            self.Curvas = canva.axes.contour(self.x, self.y, valores, levels=self.curvas_nivel, linewidths=3, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 1, alpha = 1)
                        canva.axes.grid(True)
                else:
                    # Graficación de curvas de nivel para problemas de tres dimensiones espaciales.
                    if not self.valorespecial:
                        # Graficación de curvas de nivel cuando no se especifica un valor especifico para la coordenada fija (si es que se tiene una).
                        if self.Proyeccion:
                            canva.axes.proyeccion.set_alpha(0.4)
                            if self.Coordenadas == "Cartesianas":
                                # Curvas de nivel en proyecciones de coordenadas cartesianas.
                                self.Curvas = canva.axes.contour(self.x, self.y, self.Valores[anim.deslizador.val], levels=self.curvas_nivel, linewidths=3, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 1, alpha = 1)
                            else:
                                # Curvas de nivel en proyecciones que no sean coordenadas cartesianas.
                                self.Curvas = canva.axes.contour(self.v, self.u, self.Valores[anim.deslizador.val], levels=self.curvas_nivel, linewidths=3, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 1, alpha = 1)
                            canva.axes.grid(True)
                        else:
                            # Curvas de nivel en graficas sin proyección.
                            canva.axes.superficie.set_alpha(0.4)
                            self.Curvas = canva.axes.contour(self.x, self.y, self.Valores[anim.deslizador.val], levels=self.curvas_nivel, linewidths=3, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 1, alpha = 1)
                            canva.axes.grid(True)
                    else:
                        # Graficación de curvas de nivel cuando se especifica un valor especifico para la coordenada fija (si es que se tiene una).
                        if self.Proyeccion:
                            canva.axes.proyeccion.set_alpha(0.4)
                            if self.Coordenadas == "Cartesianas":
                                # Curvas de nivel en proyecciones de coordenadas cartesianas.
                                self.Curvas = canva.axes.contour(self.x, self.y, valores, levels=self.curvas_nivel, linewidths=3, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 1, alpha = 1)
                            else:
                                # Curvas de nivel en proyecciones que no sean coordenadas cartesianas.
                                self.Curvas = canva.axes.contour(self.v, self.u, valores.T, levels=self.curvas_nivel, linewidths=3, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 1, alpha = 1)
                            canva.axes.grid(True)
                        else:
                            canva.axes.superficie.set_alpha(0.4)
                            if self.Coordenadas == "Cartesianas":
                                # Curvas de nivel en graficas de coordenadas cartesianas.
                                self.Curvas = canva.axes.contour(self.x, self.y, valores, levels=self.curvas_nivel, linewidths=2, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 1, alpha = 1)
                            else:
                                # Curvas de nivel en graficas que no sean en coordenadas cartesianas.
                                self.Curvas = canva.axes.contour(self.x, self.y, valores.T, levels=self.curvas_nivel, linewidths=2, cmap = self.Colormap, vmin = -self.Cota, vmax = self.Cota, zorder = 1, alpha = 1)
                            canva.axes.grid(True)

                if not guardado:
                    # Creación de la leyenda cuando no se guarda la animación.
                    # El acomodo horizontal de las leyendas fue tomado de roschach. (04 de marzo de 2019). Respuesta a la pregunta "Matplotlib: how to show legend elements horizontally?". stackoverflow. https://stackoverflow.com/a/54870776
                    # La localización de la leyenda entera así como su tamaño respecto de la ventana fue tomado de Kington, J. (15 de enero de 2011). Respuesta a la pregunta "How to put the legend outside the plot". stackoverflow. https://stackoverflow.com/a/4701285.
                    # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 4.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/4.0/
                    self.Ui_Etiquetas.MostrarEtiqueta.axes.legend(curvas_especificas[:-1], curvas_etiquetas[:-1], labelcolor="white", facecolor=(0.52, 0.50, 0.49, 1.0), loc="upper left", ncol=int((len(curvas_especificas)+1)/3), bbox_to_anchor=(0, 0, 1, 1), mode = "expand", fontsize='x-large', edgecolor=(0.52, 0.50, 0.49, 1.0), framealpha=1, markerscale=1.5)
                    # Actualización de la leyenda en caso de que no se esté guardando la animación.
                    self.Ui_Etiquetas.MostrarEtiqueta.figura.canvas.draw_idle()
                    # Actualización del lienzo de la gráfica.
                    canva.figura.canvas.draw_idle()
                
                if len(self.Curvas.collections) == 0:
                    # Si no se encuentran curvas, se establece este valor en Falso para evitar errores al tratar de eliminar las curvas.
                    self.curvasdibujadas = False
                    self.VentanaEtiquetas.setHidden(True)
            except:
                exctype, value, line = sys.exc_info()[:3]
                print(exctype, value, line.tb_lineno)
            
                self.curvasdibujadas = False
                raise Exception
                
            return canva.figura

    def despliegueCoeficiente_CambioExpresion(self, subproblema):
        """
        Despliega el primer coeficiente del subproblema deseado.
        
        Parámetros
        ----------
        subproblema: entero
            Número del subproblema del que se quieren obtener los coeficientes.
        """

        print(self.Soluciones)

        # Establecimiento de los indice posibles para el primer conjunto de valores propios del subproblema.
        self.ValorPropio1.setMaximum(int(self.NumeroTerminos[subproblema-1][0][1]))
        self.ValorPropio1.setMinimum(int(self.NumeroTerminos[subproblema-1][0][0]))

        if len(self.NumeroTerminos[subproblema-1]) >= 2:
            self.ValorPropio2.setEnabled(True)
            self.label_5.setEnabled(True)
            self.ValorPropio2.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(255, 255, 255)")
            self.ValorPropio2.setVisible(True)
            self.label_5.setVisible(True)

            if len(self.NumeroTerminos[subproblema-1]) == 3:
                self.ValorPropio3.setEnabled(True)
                self.label_5_1.setEnabled(True)
                self.ValorPropio3.setStyleSheet(u"color: rgb(11, 61, 98); background-color: rgb(255, 255, 255)")
                self.ValorPropio3.setVisible(True)
                self.label_5_1.setVisible(True)
            else:
                self.ValorPropio3.setEnabled(False)
                self.label_5_1.setEnabled(False)
                self.ValorPropio3.setStyleSheet(u"color: rgba(11, 61, 98, 0.9); background-color: rgba(255, 255, 255, 0.9); border-color: rgba(255, 255, 255, 0.9)")
                self.ValorPropio3.setVisible(False)
                self.label_5_1.setVisible(False)
        else:
            self.ValorPropio2.setEnabled(False)
            self.label_5.setEnabled(False)
            self.ValorPropio2.setStyleSheet(u"color: rgba(11, 61, 98, 0.9); background-color: rgba(255, 255, 255, 0.9); border-color: rgba(255, 255, 255, 0.9)")
            self.ValorPropio2.setVisible(False)
            self.label_5.setVisible(False)

        if self.ValorPropio2.isEnabled():
            # Establecimiento de los indice posibles para el segundo conjunto de valores propios del subproblema.
            if self.NumeroTerminos[subproblema-1][1][0] == "-n":
                self.ValorPropio2.setMaximum(int(self.ValoresPropios[self.Subproblema.value()-1][0][0]))
                self.ValorPropio2.setMinimum(-int(self.ValoresPropios[self.Subproblema.value()-1][0][0]))
            else:
                self.ValorPropio2.setMaximum(int(self.NumeroTerminos[subproblema-1][1][1]))
                self.ValorPropio2.setMinimum(int(self.NumeroTerminos[subproblema-1][1][0]))

            if self.ValorPropio3.isEnabled():
                # Establecimiento de los indice posibles para el segundo conjunto de valores propios del subproblema.
                if self.NumeroTerminos[subproblema-1][2][0] == "-n":
                    self.ValorPropio3.setMaximum(int(self.ValoresPropios[self.Subproblema.value()-1][0][0]))
                    self.ValorPropio3.setMinimum(-int(self.ValoresPropios[self.Subproblema.value()-1][0][0]))
                else:
                    self.ValorPropio3.setMaximum(int(self.NumeroTerminos[subproblema-1][2][1]))
                    self.ValorPropio3.setMinimum(int(self.NumeroTerminos[subproblema-1][2][0]))


        # Despliegue del primer coeficiente de la solución al subproblema requerido.
        if self.ValorPropio2.isEnabled():
            if not self.ValorPropio3.isEnabled():
                if self.NumeroTerminos[subproblema-1][1][0] == "-n":
                    self.despliegueCoeficiente_CambioValorPropio(int(self.NumeroTerminos[subproblema-1][0][0]), -int(self.NumeroTerminos[subproblema-1][0][0]), None)
                else:
                    self.despliegueCoeficiente_CambioValorPropio(int(self.NumeroTerminos[subproblema-1][0][0]), int(self.NumeroTerminos[subproblema-1][1][0]), None)
            else:
                if self.NumeroTerminos[subproblema-1][2][0] == "-n":
                    self.despliegueCoeficiente_CambioValorPropio(int(self.NumeroTerminos[subproblema-1][0][0]), int(self.NumeroTerminos[subproblema-1][1][0]), -int(self.NumeroTerminos[subproblema-1][0][0]))
                else:
                    self.despliegueCoeficiente_CambioValorPropio(int(self.NumeroTerminos[subproblema-1][0][0]), int(self.NumeroTerminos[subproblema-1][1][0]), int(self.NumeroTerminos[subproblema-1][2][0]))
        else:
            self.despliegueCoeficiente_CambioValorPropio(int(self.NumeroTerminos[subproblema-1][0][0]), None, None)

    def despliegueCoeficiente_CambioValorPropio(self, valorpropio1, valorpropio2, valorpropio3):
        """
        Despliega el coeficiente del término deseado del subproblema actual.
        
        Parámetros
        ----------
        valorpropio1: entero
            Indice del primer valor propio.

        valorpropio2: entero
            Indice del segundo valor propio.
        """

        print(self.Soluciones)

        coeficiente = ""

        try:
            if self.ValorPropio2.isEnabled() == False:
                # Despliegue del coeficiente cuando solo se tiene un conjunto de valores propios.
                if self.ValorPropio1.minimum() >= 0:
                    # Cuando se tienen indices no negativos.
                    if self.ValorPropio1.minimum() > 0:
                        valorpropio1 -= 1
                    print(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0])
                    if self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args != ():
                        # Obtención del coeficiente cuando el término tiene variables.
                        if self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[0].args != () and self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[1].args != () and not (type(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[0]) == core.add.Add or type(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[1]) == core.add.Add):
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[0].args[0]), self.Precision))+";"+str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[1].args[0]), self.Precision))
                        elif self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[0].args != () and self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[1].args == () and type(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0]) == core.add.Add:
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[0].args[0]), self.Precision))+";"+str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[1]), self.Precision))
                        elif self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[0].args == () and self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[1].args != () and type(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0]) == core.add.Add:
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[0]), self.Precision))+";"+str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[1].args[0]), self.Precision))
                        elif (type(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[0]) == core.add.Add) and (self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[1].args != ()):
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[0].args[0].args[0]), self.Precision))+";"+str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[0].args[1].args[0]), self.Precision))
                        elif (type(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[1]) == core.add.Add) and (self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[0].args != ()):
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[1].args[0].args[0]), self.Precision))+";"+str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[1].args[1].args[0]), self.Precision))
                        else:
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0].args[0]), self.Precision))
                    else:
                        # Obtención del coeficiente cuando el término es constante.
                        coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0]), self.Precision))
                else: 
                    # Cuando se tienen indices negativos se realiza un desplazamiento del indice para que sea no negativo.
                    valorpropio1 = valorpropio1 + int(self.NumeroTerminos[self.Subproblema.value()-1][0][0])
                    if self.Soluciones[self.Subproblema.value()-1][valorpropio1][0][0].args != ():
                        # Obtención del coeficiente cuando el término tiene variables.
                        if self.Soluciones[self.Subproblema.value()-1][valorpropio1][0][0].args[0].args != () and self.Soluciones[self.Subproblema.value()-1][valorpropio1][0][0].args[1].args != ():
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0][0].args[0].args[0]), self.Precision))+";"+str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0][0].args[1].args[0]), self.Precision))
                        else:
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0][0].args[0]), self.Precision))
                    else:
                        # Obtención del coeficiente cuando el término es constante.
                        coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][0][0]), self.Precision))
                coeficiente = str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1]), self.Precision)) + " : " + coeficiente
            elif self.ValorPropio3.isEnabled():
                if self.NumeroTerminos[self.Subproblema.value()-1][2][0] == "-n":
                    if (self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1] != self.valorpropiodependendiente):
                        # Modificación de los valores máximos y mínimos del segundo valor propio en problemas en coordenadas esféricas con dependencia acimutal.
                        self.ValorPropio3.setMaximum(int(self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1]))
                        self.ValorPropio3.setMinimum(-int(self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1]))
                        self.ValorPropio3.setValue(-int(self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1]))
                        valorpropio3 = self.ValorPropio3.value()
                        self.valorpropiodependendiente = self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1]

                if self.ValorPropio1.minimum() > 0:
                    valorpropio1 -= 1

                # Despliegue del coeficiente cuando se tienen dos conjuntos de valores propios.
                if (self.ValorPropio2.minimum() >= 0) and (self.ValorPropio3.minimum() >= 0):
                    # Cuando ambos conjuntos de valores propios tienen indices no negativos.
                    if self.ValorPropio2.minimum() > 0:
                        valorpropio2 -= 1
                    if self.ValorPropio3.minimum() > 0:
                        valorpropio3 -= 1
                    
                    print(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3])
                    if self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args != (): 
                        # Obtención del coeficiente cuando el término tiene variables.
                        if self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0].args != () and self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[1].args != ():
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0].args[0]), self.Precision))+";"+str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[1].args[0]), self.Precision))
                        else:
                            if I in self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args:
                                coeficiente = str(latex(I*np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0]), self.Precision)))
                            else:
                                coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0]), self.Precision))
                    else:
                        # Obtención del coeficiente cuando el término es constante.
                        coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3]), self.Precision))
                elif (self.ValorPropio2.minimum() >= 0) and (self.ValorPropio3.minimum() < 0):
                    # Cuando se tienen indices negativos en el segundo conjunto de valores propios se realiza un desplazamiento del indice para que sea no negativo.
                    if self.NumeroTerminos[self.Subproblema.value()-1][2][0] == "-n":
                        valorpropio3 = valorpropio3 + abs(self.ValorPropio3.minimum())
                        print(valorpropio2)
                    else:
                        valorpropio3 = valorpropio3 + int(self.NumeroTerminos[self.Subproblema.value()-1][2][0])
                    if self.ValorPropio2.minimum() > 0:
                        valorpropio2 -= 1

                    print(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3])
                    if self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args != ():
                        # Obtención del coeficiente cuando el término tiene variables.
                        if self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0].args != () and self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[1].args != ():
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0].args[0]), self.Precision))+";"+str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[1].args[0]), self.Precision))
                        else:
                            if I in self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args:
                                coeficiente = str(latex(I*np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0]), self.Precision)))
                            else:
                                coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0]), self.Precision))
                    else:
                        # Obtención del coeficiente cuando el término es constante.
                        coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3]), self.Precision))
                elif (self.ValorPropio2.minimum() < 0) and (self.ValorPropio3.minimum() >= 0):
                    # Cuando se tienen indices negativos en el primer conjunto de valores propios se realiza un desplazamiento del indice para que sea no negativo.
                    valorpropio2 = valorpropio2 + int(self.NumeroTerminos[self.Subproblema.value()-1][1][0])
                    if self.ValorPropio3.minimum() > 0:
                        valorpropio3 -= 1
                    if self.Soluciones[self.Subproblema.value()-1][valorpropio1-1][valorpropio2][valorpropio3].args != ():
                        # Obtención del coeficiente cuando el término tiene variables.
                        if self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0].args != () and self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[1].args != ():
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0].args[0]), self.Precision))+";"+str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[1].args[0]), self.Precision))
                        else:
                            if I in self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args:
                                coeficiente = str(latex(I*np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0]), self.Precision)))
                            else:
                                coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0]), self.Precision))
                    else:
                        # Obtención del coeficiente cuando el término es constante.
                        coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3]), self.Precision))
                elif (self.ValorPropio2.minimum() < 0) and (self.ValorPropio3.minimum() < 0):
                    # Cuando se tienen indices negativos en ambos conjuntos de valores propios se realiza un desplazamiento de los indices para que sean no negativos.
                    valorpropio2 = valorpropio2 + int(self.NumeroTerminos[self.Subproblema.value()-1][1][0])
                    valorpropio3 = valorpropio3 + int(self.NumeroTerminos[self.Subproblema.value()-1][2][0])
                    if self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args != ():
                        # Obtención del coeficiente cuando el término tiene variables.
                        if self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0].args != () and self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[1].args != ():
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0].args[0]), self.Precision))+";"+str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[1].args[0]), self.Precision))
                        else:
                            if I in self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args:
                                coeficiente = str(latex(I*np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0]), self.Precision)))
                            else:
                                coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3].args[0]), self.Precision))
                    else:
                        # Obtención del coeficiente cuando el término es constante.
                        coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2][valorpropio3]), self.Precision))

                if self.dependencia and (self.Subproblema.value()-1 in self.indicesdependencia):
                    if self.bidependencia:
                        coeficiente = str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1]), self.Precision)) + ", " + str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][1][valorpropio1][valorpropio2]), self.Precision)) +", "+ str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][2][valorpropio1][valorpropio3]), self.Precision)) + " : " + coeficiente
                    else:
                        coeficiente = str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1]), self.Precision)) +", "+ str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][1][valorpropio1][valorpropio2]), self.Precision)) +", "+ str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][2][valorpropio3]), self.Precision)) + " : " + coeficiente
                else:
                    coeficiente = str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1]), self.Precision)) +", "+ str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][1][valorpropio2]), self.Precision))+", "+ str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][2][valorpropio3]), self.Precision)) + " : " + coeficiente
            else:
                if self.NumeroTerminos[self.Subproblema.value()-1][1][0] == "-n":
                    if (self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1] != self.valorpropiodependendiente):
                        # Modificación de los valores máximos y mínimos del segundo valor propio en problemas en coordenadas esféricas con dependencia acimutal.
                        self.ValorPropio2.setMaximum(int(self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1]))
                        self.ValorPropio2.setMinimum(-int(self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1]))
                        self.ValorPropio2.setValue(-int(self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1]))
                        valorpropio2 = self.ValorPropio2.value()
                        self.valorpropiodependendiente = self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1]

                # Despliegue del coeficiente cuando se tienen dos conjuntos de valores propios.
                if (self.ValorPropio1.minimum() >= 0) and (self.ValorPropio2.minimum() >= 0):
                    # Cuando ambos conjuntos de valores propios tienen indices no negativos.
                    if self.ValorPropio1.minimum() > 0:
                        valorpropio1 -= 1
                    if self.ValorPropio2.minimum() > 0:
                        valorpropio2 -= 1
                    
                    print(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2])
                    if self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args != (): 
                        # Obtención del coeficiente cuando el término tiene variables.
                        if self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0].args != () and self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[1].args != ():
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0].args[0]), self.Precision))+";"+str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[1].args[0]), self.Precision))
                        else:
                            if I in self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args:
                                coeficiente = str(latex(I*np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0]), self.Precision)))
                            else:
                                coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0]), self.Precision))
                    else:
                        # Obtención del coeficiente cuando el término es constante.
                        coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2]), self.Precision))
                elif (self.ValorPropio1.minimum() >= 0) and (self.ValorPropio2.minimum() < 0):
                    # Cuando se tienen indices negativos en el segundo conjunto de valores propios se realiza un desplazamiento del indice para que sea no negativo.
                    if self.NumeroTerminos[self.Subproblema.value()-1][1][0] == "-n":
                        valorpropio2 = valorpropio2 + abs(self.ValorPropio2.minimum())
                        print(valorpropio2)
                    else:
                        valorpropio2 = valorpropio2 + int(self.NumeroTerminos[self.Subproblema.value()-1][1][0])
                    if self.ValorPropio1.minimum() > 0:
                        valorpropio1 -= 1

                    print(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2])
                    if self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args != ():
                        # Obtención del coeficiente cuando el término tiene variables.
                        if self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0].args != () and self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[1].args != ():
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0].args[0]), self.Precision))+";"+str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[1].args[0]), self.Precision))
                        else:
                            if I in self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args:
                                coeficiente = str(latex(I*np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0]), self.Precision)))
                            else:
                                coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0]), self.Precision))
                    else:
                        # Obtención del coeficiente cuando el término es constante.
                        coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2]), self.Precision))
                elif (self.ValorPropio1.minimum() < 0) and (self.ValorPropio2.minimum() >= 0):
                    # Cuando se tienen indices negativos en el primer conjunto de valores propios se realiza un desplazamiento del indice para que sea no negativo.
                    valorpropio1 = valorpropio1 + int(self.NumeroTerminos[self.Subproblema.value()-1][0][0])
                    if self.ValorPropio2.minimum() > 0:
                        valorpropio2 -= 1
                    if self.Soluciones[self.Subproblema.value()-1][valorpropio1-1][valorpropio2].args != ():
                        # Obtención del coeficiente cuando el término tiene variables.
                        if self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0].args != () and self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[1].args != ():
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0].args[0]), self.Precision))+";"+str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[1].args[0]), self.Precision))
                        else:
                            if I in self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args:
                                coeficiente = str(latex(I*np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0]), self.Precision)))
                            else:
                                coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0]), self.Precision))
                    else:
                        # Obtención del coeficiente cuando el término es constante.
                        coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2]), self.Precision))
                elif (self.ValorPropio1.minimum() < 0) and (self.ValorPropio2.minimum() < 0):
                    # Cuando se tienen indices negativos en ambos conjuntos de valores propios se realiza un desplazamiento de los indices para que sean no negativos.
                    valorpropio1 = valorpropio1 + int(self.NumeroTerminos[self.Subproblema.value()-1][0][0])
                    valorpropio2 = valorpropio2 + int(self.NumeroTerminos[self.Subproblema.value()-1][1][0])
                    if self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args != ():
                        # Obtención del coeficiente cuando el término tiene variables.
                        if self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0].args != () and self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[1].args != ():
                            coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0].args[0]), self.Precision))+";"+str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[1].args[0]), self.Precision))
                        else:
                            if I in self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args:
                                coeficiente = str(latex(I*np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0]), self.Precision)))
                            else:
                                coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2].args[0]), self.Precision))
                    else:
                        # Obtención del coeficiente cuando el término es constante.
                        coeficiente = str(np.round(float(self.Soluciones[self.Subproblema.value()-1][valorpropio1][valorpropio2]), self.Precision))

                if self.dependencia  and (self.Subproblema.value()-1 in self.indicesdependencia):
                    if self.invertir:
                        coeficiente = str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][1][valorpropio2][valorpropio1]), self.Precision)) +", "+ str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio2]), self.Precision)) + " : " + coeficiente
                    else:
                        coeficiente = str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1]), self.Precision)) +", "+ str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][1][valorpropio1][valorpropio2]), self.Precision)) + " : " + coeficiente
                else:
                    coeficiente = str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][0][valorpropio1]), self.Precision)) +", "+ str(np.round(float(self.ValoresPropios[self.Subproblema.value()-1][1][valorpropio2]), self.Precision)) + " : " + coeficiente
        except:
            # Interpretación del tipo de error.
            tipoError, explicacion, line = sys.exc_info()[:3]
            print(tipoError)
            print(explicacion)
            print(line.tb_lineno)
        
        # Las siguientes líneas fueron tomadas de
        # mugiseyebrows. (31 de marzo 2021). Respuesta a la pregunta "MathJax flickering and statusbar showing in PyQt5". stackoverflow. https://stackoverflow.com/a/66870093
        # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 4.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/4.0/
        # Intercambio de \\ por \\\\ para la interpretación en formato LaTeX.
        coeficiente = coeficiente.replace("\\","\\\\")
        # Despliegue del coeficiente.
        self.pagina.runJavaScript('convert("{}");'.format(coeficiente))

        self.CurvasNivelAuto.setShortcut("Ctrl+A")

    def activarCurvas(self, boton):
        """
        Activa y desactiva la exclusividad de los botones de curvas de nivel para permitir elegir una o ninguna de ellas.

        Parámetros
        ----------
        boton: QPushButton
            Boton presionado.
        """

        # La siguiente línea de código fue tomada de eyllanesc. (21 de marzo de 2021). Respuesta a la pregunta "Uncheck all boxes in exclusive group". stackoverflow. https://stackoverflow.com/a/66728385
        # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 4.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/4.0/
        self.Grupo.setExclusive(not boton.isChecked())
        self.CurvasNivelAuto.setShortcut("Ctrl+A")

    def calcularValorSolucion(self):
        """Calcular y muestra el valor de la solución en el punto especificado por el usuario."""

        if self.inicio:
            self.inicio = False

            return None

        resultado = ""
        try:
            if not self.Coordenada3.isEnabled():
                if not self.dependencia_tiempo:
                    if (float(parsing.parse_expr(self.Coordenada1.text())) > self.dominio[1]) or (float(parsing.parse_expr(self.Coordenada1.text())) < self.dominio[0]) or (float(parsing.parse_expr(self.Coordenada2.text())) > self.dominio[3]) or (float(parsing.parse_expr(self.Coordenada2.text())) < self.dominio[2]):
                    # Si alguna de las dos primeras coordenadas está fuera del dominio no se calcula el valor.
                        resultado = "\\\\text{El punto no está en el dominio.}"
                else:
                    if (float(parsing.parse_expr(self.Coordenada1.text())) > self.dominio[1]) or (float(parsing.parse_expr(self.Coordenada1.text())) < self.dominio[0]) or (float(parsing.parse_expr(self.Coordenada2.text())) < 0):
                    # Si alguna de las dos primeras coordenadas está fuera del dominio no se calcula el valor (en problemas temporales).
                        resultado = "\\\\text{El punto no está en el dominio.}"
            elif self.Coordenada3.isEnabled():
                if not self.dependencia_tiempo:
                    if (float(parsing.parse_expr(self.Coordenada3.text())) > self.dominio[5]) or (float(parsing.parse_expr(self.Coordenada3.text())) < self.dominio[4]):
                        # Si la tercera coordenada está dentro del dominio o se calcula el valor.
                        resultado = "\\\\text{El punto no está en el dominio.}"
                else:
                    if float(parsing.parse_expr(self.Coordenada3.text())) < 0:
                        # Si la tercera coordenada está dentro del dominio o se calcula el valor (problemas temporales).
                        resultado = "\\\\text{El punto no está en el dominio.}"
            if resultado == "":
                # Calculo del valor de la solución.
                if self.Coordenada3.isEnabled() == False:
                    valor_solucion = self.Funcion(float(parsing.parse_expr(self.Coordenada1.text())), float(parsing.parse_expr(self.Coordenada2.text()))) 
                else:
                    valor_solucion = self.Funcion(float(parsing.parse_expr(self.Coordenada1.text())), float(parsing.parse_expr(self.Coordenada2.text())), float(parsing.parse_expr(self.Coordenada3.text())))
                # Redondeo del valor de la solución.
                valor_solucion = np.round(valor_solucion, self.Precision)

                # La siguiente línea fue tomada de
                # mugiseyebrows. (31 de marzo 2021). Respuesta a la pregunta "MathJax flickering and statusbar showing in PyQt5". stackoverflow. https://stackoverflow.com/a/66870093
                # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 4.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/4.0/
                # Despliegue del valor.
                self.pagina2.runJavaScript('convert("{}");'.format(valor_solucion))
            else:
                # Las siguiente línea fue tomada de
                # mugiseyebrows. (31 de marzo 2021). Respuesta a la pregunta "MathJax flickering and statusbar showing in PyQt5". stackoverflow. https://stackoverflow.com/a/66870093
                # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 4.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/4.0/
                self.pagina2.runJavaScript('convert("{}");'.format(resultado))
        except:
            tipoError, explicacion, line = sys.exc_info()[:3]
            print(tipoError)
            print(explicacion)
            print(line.tb_lineno)

            # La siguiente línea fuer tomada de
            # mugiseyebrows. (31 de marzo 2021). Respuesta a la pregunta "MathJax flickering and statusbar showing in PyQt5". stackoverflow. https://stackoverflow.com/a/66870093
            # El uso de esta respuesta está licenciado bajo la licencia CC BY-SA 4.0 la cual puede ser consultada en https://creativecommons.org/licenses/by-sa/4.0/
            self.pagina2.runJavaScript('convert("{}");'.format("\\\\text{Hay un error en la entrada.}"))
        
class Indicadores(QtCore.QObject):
    """Clase que contiene las señales necesarias para la ejecución de las tareas de graficación."""
    
    finalizar_signal = pyqtSignal(str)
    avanzar_signal = pyqtSignal(str)
    error_signal = pyqtSignal(tuple)
    guardar_signal = pyqtSignal()
    proyeccion_signal = pyqtSignal()
    curvas_signal = pyqtSignal()
    corte_signal = pyqtSignal()
    coordenada_signal = pyqtSignal()

class Conteo(QtCore.QObject):
    """
    Clase que contiene una variable auxiliar que funciona como conteo.
    """

    def __init__(self):
        # El nombre de la variable permite la compatibilidad de la función graficadora de curvas de nivel en el proceso de guardado.
        self.val = -2

# ------ Ejecución de la aplicación
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_Graficacion(MainWindow)
    MainWindow.show()
    ret = app.exec_()
    #atexit.register(ui.limpiargrafica)
    sys.exit(ret) 