"""
Authors: Francisca Rodrigues, Rafaela Oliveira, Rita Mendes

Usage: Programa realiza um pequeno osciloscópio com o auxílio dos ficheiros 'T_Display.py' e 'T_Simulator.py'.
Inicializa um display com uma grelha de 10 divisões na horizontal e 6 na vertical, realiza uma leitura de valores do ADC convertendo-os
para tensões e representando a forma de onda sobre a grelha. Para além disso, o utilizador dispõe de 2 butões que têm 3 opções de clicks: normal, prolongado e duplo.
Consoante o click, o utilizador pode alterar as escalas vertical ou horizotal, ver algumas medições relevantes e/ou enviá-las por email e também fazer um Autoscale (funcionalidade adicional)
que tem o objetivo de determinar e aplicar qual a melhor escala para a visualização do sinal.

"""
import T_Display
import math

# Variáveis Globais
tft = T_Display.TFT()  # Instancia um objeto da classe TFT
escala_horizontal = [5, 10, 20, 50]  # escala temporal, em ms
escala_vertical = [1, 2, 5, 10]  # escala da amplitude, em volts
fator = 1/29.3  # Fator do divisor resistivo
width = 240
height = 135
raiz = math.sqrt(2)
raiz3 = math.sqrt(3)
index_vertical = 2  # posição default escala vertical
index_horizontal = 1  # posição default escala horizontal


def reset_screen():
    """ 
        Summary: Função que reinicia o ecrã, ou seja, apaga o display, desenha a grelha e adiciona 
        o icon de wifi
    """

    tft.display_set(tft.BLACK, 0, 0, width, height)  # Apaga display
    tft.display_write_grid(0, 0, width, height-16, 10, 6,
                           tft.GREY1, tft.GREY2)  # Desenha grelha
    tft.set_wifi_icon(width-16, height-16)  # Adiciona wifi icon


def write_scale(index_vertical, index_horizontal):
    """ 
        Summary: Função que recebe a escala e imprime-a no topo do display

        Args:
            index_vertical (integer): index da escala vertical
            index_horizontal (integer): index da escala horizontal
    """
    tft.display_write_str(tft.Arial16, "%d ms/div" %
                          escala_horizontal[index_horizontal], 0, height-16)
    tft.display_write_str(tft.Arial16, "%d V/div" %
                          escala_vertical[index_vertical], 45+35, height-16)


def identify_wave(y, max):
    """
        Summary: Identifica o tipo de onda do gráfico, ou seja, se é sinusoidal, retangular ou triangular para podemos
        calcular corretamente o valor eficaz.

        Args:
            y (array): array de posições verticais do gráfico 
            max (int): abcissa do primeiro máximo de amplitude encontrado

        Returns:
            integer: 1,2,3 consoante é sinusoidal, retangular ou triangular, respetivamente
    """
    dif_num = 0
    # se for horizontal, entao o array y so tem 2 valores diferentes
    for i in range(len(y)):
        is_new = True
        for j in range(i+1, len(y)):
            if y[i] == y[j]:
                is_new = False
                break
        if is_new:
            dif_num += 1
    if (dif_num == 2):  # se so tiver 2 valores diferentes
        return 2  # sinal retangular

    # se for triangular, entao o array y tem um "pico"
    if (y[max+1] != y[max] and y[max-1] != y[max]):
        return 3  # sinal triangular

    # se nao for retangular nem triangular, é sinusoidal
    return 1  # sinal sinusoidal


def read_and_display(index_vertical, index_horizontal, readOnly):
    """
        Summary: Função de leitura dos valores do ADC e representação no display (consoante flag readOnly)

        Args:
            index_vertical (integer): index da escala vertical
            index_horizontal (integer): index da escala horizontal
            readOnly (integer): flag que toma os valores de 0 ou 1, se for 1, então não pretendemos fazer a representação no display

        Returns:
            Vmax(integer): valor maximo de amplitude 
            Vmin(integer): valor minimo de amplitude 
            Vmed(integer): valor médio de amplitude 
            Vrms(integer): valor eficaz de amplitude
            tensoes_aux(array): array com todas as tensoes
    """
    pontos_adc = tft.read_adc(width, escala_horizontal[index_horizontal]*10)
    tensoes_aux = pontos_adc
    Vmax = 0
    Vmin = 0
    Vmed = 0
    Vrms = 0
    Vmax_x = 0  # posicao x de Vmax
    x = []
    y = []
    for n in range(width):
        # Converte valor do ADC em Volt (Calibração do professor)
        V = 0.00044028 * pontos_adc[n] + 0.091455
        # V= ... NOSSA CALIBRAÇÃO
        V = V - 1                                 # Tensão entrada de referência de 1V
        V = V / fator                             # Entra com o efeito do div. resistivo
        tensoes_aux[n] = V
        pixel = (height-16)/2 + (
            (height-16)/(6*escala_vertical[index_vertical]))*V
        if pixel > height-16:  # Quando o valor excede o espaço vertical superior simplesmente fica no limite superior do display
            pixel = height-16
        if pixel < 0:   # Quando o valor excede o espaço vertical inferior simplesmente fica no limite inferior do display
            pixel = 0

        x.append(n)
        y.append(round(pixel))

        if n == 0:       # Caso seja o primeiro ponto
            Vmax = Vmin = Vmed = Vrms = V
            Vmax_x = n
        else:
            Vmed += V
            if V > Vmax:
                Vmax = V
                Vmax_x = n
            if V < Vmin:
                Vmin = V

    # se so quisermos ler (readOnly = 1), nao imprimimos no display
    if readOnly == 0:
        reset_screen()
        tft.display_nline(tft.YELLOW, x, y)

    Vrms=0
    for i in range(len(tensoes_aux)):
        Vrms += (tensoes_aux[i]*tensoes_aux[i])

    Vrms = math.sqrt(Vrms / len(tensoes_aux))
    Vmed /= 240  # Divide pelo número de amostras

    write_scale(index_vertical, index_horizontal)

    return Vmax, Vmin, Vmed, Vrms, tensoes_aux


def get_period(index_vertical, index_horizontal):
    """
        Summary: calcula o periodo de um sinal, fazendo a diferença entre dois valores máximos (picos) sucessivos

        Args:
            index_vertical (integer): index da escala vertical
            index_horizontal (integer): index da escala horizontal

        Returns:
            int: retorna o valor de 1 periodo
    """
    temp = -1
    count = 0
    max_value, min_value, med_value, rms_value, tensoes_array = read_and_display(
            index_vertical, index_horizontal, 1)

    for i in range(len(tensoes_array)):  # percorrer todas as tensões
        aux1 = True
        aux2 = False
        zeros = []
        periodo=0
        if (tensoes_array[i] < 0.01 and tensoes_array[i] > -0.01):
            print("kjasdsn")
            print(len(zeros))
            print(zeros)
            if (len(zeros) == 0):
                print("olaaolaoala")
                print(i)
                zeros.append(i)
            else:
                print("help")
                zeros.append(i-zeros[i-1])

    for i in range(len(zeros)):
        periodo += zeros[i]

    periodo = (2* (periodo / len(zeros))) * ((escala_horizontal[index_horizontal]*10) / width)*0.001
    print(periodo)


def auto_scale(escala, x, div):
    """
        Summary: Função que trata do autoscale, para isso vai selecionar as escalas possiveis e ver qual delas se aproxima
        mais do valor que queremos representar. Com escalas possiveis queremos dizer, por exemplo: 
        - Se quisermos representar uma amplitude de 5V nas 3 divisoes disponiveis, é impossivel escolher a escala 1V/div, porque
        esta representa no máximo 3 volts. Assim, as escalas possiveis seriam: [2 5 10]V/div
        - Após esta seleção, vamos ver qual das escalas se aproxima mais da amplitude que queremos representar, neste caso:
        2V x 3div = 6V ; 5V x 3div = 15V ; 10V x 3div = 30V => [6 15 30] Destes 3 valores, o que mais se aproxima de 5V é o 6V,
        Logo, a escala a usar é 2V/div. 

        Args:
            escala (array): array da escala vertical ou horizontal
            x (int): valor que queremos representar
            div (int): numero de divisões que temos para representar o valor x

        Returns:
            int: index da escala (vertical/horizontal) que melhor representa o valor x
    """
    aux_array = []
    for i in range(len(escala)):  # percorrer o array da escala
        if (escala[i]*div >= x):  # selecionar as escalas possíveis
            aux_array.append(escala[i])

    # retornar a escala que mais se aproxima de x
    return find_closest_number(aux_array, x, div)


def find_closest_number(array, x, div):
    """
        Summary: Percorre um array e vê qual das escalas corresponde à menor distância entre o valor x e
        ao produto da escala pelas divisões

        Args:
            array (array): array de escalas possiveis
            x (int): valor que queremos representar
            div (int): numero de divisões que temos para representar o valor x

        Returns:
            int: indice da escala mais indicada
    """
    closest = None
    min_diff = float('inf')  # inicializar com um valor muito grande (infinito)

    for i in range(len(array)):
        product = array[i] * div
        diff = abs(product - x)  # calcular a diferença

        # encontrar a diferença minima de forma a encontrar a escala mais adequada
        if diff < min_diff:
            min_diff = diff
            closest = array[i]

    # encontrar o indice ao qual essa escala corresponde
    if (div == 3):  # trata-se da escala vertical
        for i in range(len(escala_vertical)):
            if (closest == escala_vertical[i]):
                return i
    else:  # trata-se da escala horizontal
        for i in range(len(escala_horizontal)):
            if (closest == escala_horizontal[i]):
                return i


# Programa principal (main)
max_value, min_value, med_value, rms_value, tensoes_array = read_and_display(
    index_vertical, index_horizontal, 0)

while tft.working():  # Ciclo principal do programa
    but = tft.readButton()                          # Lê estado dos botões
    if but != tft.NOTHING:
        print("Button pressed:", but)
        if but == 11:  # Button 1 click - Repete função
            max_value, min_value, med_value, rms_value, tensoes_array = read_and_display(
                index_vertical, index_horizontal, 0)

        if but == 12:  # Button 2 click prolongado - Envia mail
            max_value, min_value, med_value, rms_value, tensoes_array = read_and_display(
                index_vertical, index_horizontal, 1)

            corpo_mail = "Lista de %d pontos em %.2f segundos.\n Vmax = %.3fV \t\t Vmin = %.3fV \n Vmed = %.3fV \t\t Vrms = %.3fV\n" % (
                width, (escala_horizontal[index_horizontal]*10)*0.001, max_value, min_value, med_value, rms_value)
            tft.send_mail(((escala_horizontal[index_horizontal]*10)*0.001)/width, tensoes_array, corpo_mail,
                          "rcordeiromendes@gmail.com")

        # Button 1 duplo click - Apresenta os valores de medida e o periodo (adicional)
        if but == 13:
            T = get_period(index_vertical, index_horizontal)
            tft.display_set(tft.BLACK, 0, 0, width, height)  # apagar display
            # escrever as medidas no display
            tft.display_write_str(
                tft.Arial16, "Medidas", 70, 90, tft.CYAN)
            tft.display_write_str(
                tft.Arial16, "Min: %.2f V" % min_value, 5, 50)
            tft.display_write_str(tft.Arial16, "Max: %.2f V" %
                                  max_value, 130, 50)
            tft.display_write_str(
                tft.Arial16, "Med: %.2f V" % med_value, 5, 70)
            tft.display_write_str(tft.Arial16, "RMS: %.2f V" %
                                  rms_value, 130, 70)
            tft.display_write_str(tft.Arial16, "T = %.2f ms" %
                                  (T*1000), 5, 30)

        if but == 21:            # Button 2 click - Alterar a escala vertical
            index_vertical += 1
            if (index_vertical > 3):  # alterar a escala vertical de forma circular
                index_vertical = 0
            max_value, min_value, med_value, rms_value, tensoes_array = read_and_display(
                index_vertical, index_horizontal, 0)

        if but == 22:            # Button 2 click prolongado - Alterar a escala horizontal
            index_horizontal += 1
            if (index_horizontal > 3):  # alterar a escala horizontal de forma circular
                index_horizontal = 0
            max_value, min_value, med_value, rms_value, tensoes_array = read_and_display(
                index_vertical, index_horizontal, 0)

        if but == 23:  # Button 2 double click - Autoscale
            T = get_period(index_vertical, index_horizontal)
            max_value, min_value, med_value, rms_value, tensoes_array = read_and_display(
                index_vertical, index_horizontal, 1)
            # 3divs porque a amplitude max_value começa em 0
            index_vertical = auto_scale(escala_vertical, 1.1*max_value, 3)
            # para se ver no minimo 2 periodos quando se faz autoscale (em milisegundos)
            num_periodos = 2*T*1000
            index_horizontal = auto_scale(escala_horizontal, num_periodos, 10)

            max_value, min_value, med_value, rms_value, tensoes_array = read_and_display(
                index_vertical, index_horizontal, 0)
