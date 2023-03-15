from tkinter import *
from tkinter import messagebox
import tkinter.ttk as ttk
import src.utils.colors as colors
import src.utils.fonts as fonts
import src.utils.constants as constants
import serial
import time
import copy
import struct
from threading import Thread
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
from socket import *
import pymysql.cursors

file = 0
df = 0
s = 0
active = False

def start_gui():
    root = Tk()
    GUI_Orthesis(root)
    root.mainloop()


class Arduino:
    def __init__(self, port="COM5", baud_rate=9600, plotLx=101, d_bytes=4, numplot=2):
        self.port = port
        self.baud_rate = baud_rate
        self.plotLx = plotLx
        self.d_bytes = d_bytes
        self.numplot = numplot
        self.raw_data = bytearray(numplot * d_bytes)
        self.data_tipo = 'f'
        self.EMG1 = []
        self.EMG2 = []
        self.ANGLE = []
        self.data = []
        for i in range(numplot):
            self.data.append(collections.deque([0] * plotLx, maxlen=plotLx))
        self.isRun = True
        self.isReceiving = False
        self.thread = None
        self.plotTimer = 0
        self.previousTimer = 0
        try:
            self.ard_con = serial.Serial(port, baud_rate, timeout=1)
        except:
            messagebox.showerror("Error", "Conecte el arduino")

    def readSerialStart(self):
        if self.thread == None:
            self.thread = Thread(target=self.backgroundThread)
            self.thread.start()
            while self.isReceiving != True:
                time.sleep(0.1)

    def getSerialData(self, frame, lines, lineValueText, lineLabel, timeText):
        currentTimer = time.perf_counter()
        self.plotTimer = int((currentTimer - self.previousTimer) * 1000)  # the first reading will be erroneous
        self.previousTimer = currentTimer
        timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')
        privateData = copy.deepcopy(self.raw_data[:])  # so that the 3 values in our plots will be synchronized to the same sample time
        for i in range(self.numplot):
            data = privateData[(i * self.d_bytes):(self.d_bytes + i * self.d_bytes)]
            value, = struct.unpack(self.data_tipo, data)
            if(active):
                if(i == 0):
                    self.EMG1.append(value)
                if(i == 1):
                    self.EMG2.append(value)

            self.data[i].append(value)  # we get the latest data point and append it to our array
            lines[i].set_data(range(self.plotLx), self.data[i])
            lineValueText[i].set_text('[' + lineLabel[i] + '] = ' + str(value))

    def backgroundThread(self):  # retrieve data
        time.sleep(1.0)  # give some buffer time for retrieving data
        self.ard_con.reset_input_buffer()
        while (self.isRun):
            self.ard_con.readinto(self.raw_data)
            self.isReceiving = True

    def sendSerialData(self, data):
        self.ard_con.write(data.encode('utf-8'))

    def close(self):
        print("in")
        global file
        global df

        emg1 = []
        for i in range(len(self.EMG1)):
            newData = ['Data'+str(i+1), self.EMG1[i]]
            emg1.append(newData)

        emg2 = []
        for i in range(len(self.EMG2)):
            newData = ['Data' + str(i+1), self.EMG2[i]]
            emg2.append(newData)

        angle = []
        for i in range(len(self.ANGLE)):
            newData = ['Data' + str(i+1), self.ANGLE[i]]
            angle.append(newData)

        df2 = pd.DataFrame(emg1)
        df3 = pd.DataFrame(emg2)
        df4 = pd.DataFrame(angle)

        writer = pd.ExcelWriter(file, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Registro', index=False, header=False)
        df2.to_excel(writer, sheet_name='EMG', index=False, header=False)
        df3.to_excel(writer, sheet_name='ANGLE', index=False, header=False)
        writer.save()

        self.isRun = False
        self.thread.join()
        self.ard_con.close()
        connection = pymysql.connect(host="18.216.201.191", user="pf",
                                     passwd="123456789",
                                     db="pf")
        MyCursor = connection.cursor()
        sql = "INSERT INTO `datos`(`nombre`, `sexo`, `edad`, `peso`,`prueba`, `emg`, `angulo`) VALUES(%s,%s,%s,%s,%s,%s,%s);"
        MyCursor.execute(sql, (nombre, sexo, edad, peso, prueba, emg1, emg2))
        connection.commit()
        connection.close()
        print('Disconnected...')



class GUI_Orthesis:
    def __init__(self, root: Tk):
        # VARIABLES
        self.sexo = StringVar()
        self.sexo.set("Seleccione")
        sexo_options = ["Masculino", "Femenino"]

        self.grado = IntVar()

        self.modo_uso = StringVar()
        self.modo_uso.set("Seleccione")
        uso_options = ["Manual", "Automatico"]



        # Crear GUI
        root.title("Ortesis de codo")
        root.geometry("325x400+450+90")
        root.resizable(False, False)
        root.configure(background=colors.GRAY)
        root.configure(highlightbackground="#ffffff")
        root.configure(highlightcolor="black")

        # DATOS DEL USUARIO
        self.label_tit = Label(root, text="Datos del usuario", font=fonts.courier16b)
        self.label_tit.grid(row=1, column=0, sticky="w", padx=0, pady=10, columnspan=2)

        self.label_nombre = Label(root, text="Nombre: ", font= fonts.courier9b)
        self.label_nombre.grid(row=2, column=0, sticky="w", padx=5, pady=5 )
        self.entry_nombre = Entry(root, font=fonts.courier9,justify="center")
        self.entry_nombre.grid(row=2, column=1)

        self.label_apellido = Label(root, text="Apellido: ", font=fonts.courier9b)
        self.label_apellido.grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.entry_apellido = Entry(root, font=fonts.courier9, justify="center")
        self.entry_apellido.grid(row=3, column=1)

        self.label_edad = Label(root, text="Edad: ", font=fonts.courier9b)
        self.label_edad.grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.entry_edad = Entry(root, font=fonts.courier9, justify="center")
        self.entry_edad.grid(row=4, column=1)

        self.label_sexo = Label(root, text="Sexo: ", font=fonts.courier9b)
        self.label_sexo.grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.menu_sexo = OptionMenu(root, self.sexo, *sexo_options)
        self.menu_sexo.grid(row=5, column=1, padx=5, pady=5)

        self.label_uso = Label(root, text="Modo de uso: ", font=fonts.courier9b)
        self.label_uso.grid(row=7, column=0, sticky="w", padx=5, pady=5)
        self.menu_uso = OptionMenu(root, self.modo_uso, *uso_options)
        self.menu_uso.grid(row=7, column=1, padx=5, pady=5)

        boton_terapia = Button(root, text="Empezar terapia", background=colors.MAIN_BLUE, font=fonts.courier13b,foreground=colors.BLACK,relief=RAISED,cursor="hand2", command=self.terapia)
        boton_terapia.grid(row=8, column=0, columnspan=2, pady=20)

    def terapia(self):
        global file
        global df
        nombre = self.entry_nombre.get()
        apellido = self.entry_apellido.get()
        edad = self.entry_edad.get()
        sexo = self.sexo.get()

        ymd = time.strftime('%Y-%m-%d')
        hms = time.strftime('%H%M')
        df = pd.DataFrame([['Nombre: ', nombre], ['Apellido: ', apellido], \
                           ['Sexo: ', sexo], ['Edad: ', edad]])
        file = (apellido + '_' + nombre + '_' + ymd + '_' + hms+ '.xlsx')


        print(apellido)
        if self.modo_uso.get() == "Manual":
            real_time_plot()




class Window(Frame):
    def __init__(self, figure, master, SerialReference):
        Frame.__init__(self, master)
        self.master = master
        self.serialReference = SerialReference
        self.initWindow(figure)



    def initWindow(self, figure):
        self.master.title("Modo Manual")
        self.master.geometry("1000x600+80+30")
        self.master.resizable(False, False)
        self.frame_left = Frame(self.master)
        self.frame_left.place(relx=-0.02, rely=-0.02, relheight=1.04, relwidth=0.65)
        self.frame_left.configure(borderwidth="0")
        self.frame_left.configure(background=colors.GRAY)
        canvas = FigureCanvasTkAgg(figure, master=self.frame_left)
        ##toolbar = NavigationToolbar2Tk(canvas, self.master)
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

        ##VARIABLES
        self.velocidad = StringVar()
        self.velocidad.set("Lento")
        options_vel = ["Lento", "Normal", "Rapido"]

        self.frame_right = Frame(self.master)
        self.frame_right.place(relx=0.65, rely=-0.02, relheight=1.04, relwidth=0.35)
        self.frame_right.configure(borderwidth="0")
        self.frame_right.configure(background=colors.GRAY)

        self.label_rep = Label(self.frame_right, text="Numero de repeticiones: ", font=fonts.courier9b)
        self.label_rep.grid(row=1, column=0, sticky="w", padx=5, pady=65)
        self.entry_rep = Entry(self.frame_right, font=fonts.courier9, justify="center")
        self.entry_rep.grid(row=1, column=1)


        self.label_ini_angle = Label(self.frame_right, text="Angulo Inicial: ", font=fonts.courier9b)
        self.label_ini_angle.grid(row=2, column=0, sticky="w", padx=5, pady=35)
        self.entry_ini_angle = Entry(self.frame_right, font=fonts.courier9, justify="center")
        self.entry_ini_angle.grid(row=2, column=1)


        self.label_velocidad = Label(self.frame_right, text="Seleccione velocidad: ", font=fonts.courier9b)
        self.label_velocidad.grid(row=3, column=0, sticky="w", padx=5, pady=35)
        self.menu_velocidad = OptionMenu(self.frame_right, self.velocidad, *options_vel)
        self.menu_velocidad.grid(row=3, column=1, padx=5, pady=5)


        self.label_fin_angle = Label(self.frame_right, text="Digite el angulo final: ", font=fonts.courier9b)
        self.label_fin_angle.grid(row=4, column=0, sticky="w", padx=5, pady=35)
        self.entry_fin_angle = Entry(self.frame_right, font=fonts.courier9, justify="center")
        self.entry_fin_angle.grid(row=4, column=1)


        boton_start = Button(self.frame_right, text="Empezar", background=colors.MAIN_BLUE, font=fonts.courier13b, foreground=colors.BLACK, relief=RAISED, cursor="hand2", command=self.start)
        boton_start.grid(row=5, column=0, columnspan=2, padx=15, pady=15)

        boton_save = Button(self.frame_right, text="Guardar datos", background=colors.MAIN_BLUE, font=fonts.courier13b, foreground=colors.BLACK, relief=RAISED, cursor="hand2", command=self.detener)
        boton_save.grid(row=6, column=0, columnspan=2)

    def start(self):
        global active
        vel = self.velocidad.get()
        if (vel == "Lento"):
            velocidad = 15

        if (self.velocidad.get() == "Normal"):
            velocidad = 30

        if (self.velocidad.get() == "Rapido"):
             velocidad = 45


        self.serialReference.sendSerialData(self.entry_rep.get() + '%' + self.entry_ini_angle.get() + '%' + str(velocidad) + '%' + self.entry_fin_angle.get() + '#')
        active = True
        s.readSerialStart()


    def detener(self):
        self.serialReference.sendSerialData('S')
        self.serialReference.close()


def real_time_plot():
    global s
    global active
    s = Arduino()


    # plotting starts below
    pltInterval = 50    # Period at which the plot animation updates [ms]
    xmin = 0
    xmax = 100
    ymin = 0
    ymax = 600
    fig = plt.figure(figsize=(4, 4))
    ax = plt.axes(xlim=(xmin, xmax), ylim=(float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10)))
    ax.set_title('Señales obtenidas')
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Señales EMG")

    # put our plot onto Tkinter's GUI
    root = Tk()
    app = Window(fig, root, s)

    lineLabel = ['EMG', 'ANGULO']
    style = ['r-', 'c-']
    timeText = ax.text(0.70, 0.95, '', transform=ax.transAxes)
    lines = []
    lineValueText = []
    for i in range(2):
        lines.append(ax.plot([], [], style[i], label=lineLabel[i])[0])
        lineValueText.append(ax.text(0.70, 0.90-i*0.05, '', transform=ax.transAxes))
    anim = animation.FuncAnimation(fig, s.getSerialData, fargs=(lines, lineValueText, lineLabel, timeText), interval=pltInterval)

    plt.legend(loc="upper left")
    root.mainloop()


if __name__ == '__main__':
    start_gui()
