import matplotlib.pyplot as plt
import numpy as np

# Настройки для читаемых графиков
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['legend.fontsize'] = 11
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['figure.dpi'] = 100

# Данные из диплома (таблицы)

# График 1: доли этапов (таблица 4)
stages = ['_build_and_generate_test_code', 'refine', '_run_analysis', '_merge_and_write_results', 'Прочие']
times = [18.23, 35.05, 129.75, 2.12, 507.19 - (18.23+35.05+129.75+2.12)]  # остаток 322.04
colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99','#c2c2f0']

def plot_pie():
    plt.figure()
    plt.pie(times, labels=stages, autopct='%1.1f%%', startangle=90, colors=colors)
    plt.title('Распределение времени по этапам пайплайна', fontweight='bold')
    plt.tight_layout()
    plt.savefig('graph1_pie.png')
    plt.show()

# График 2: масштабируемость по воркерам
workers = [1, 2, 3, 4]
times_workers = [594.27, 397.26, 389.78, 325.96]
ideal = [times_workers[0]/w for w in workers]

def plot_scalability():
    plt.figure(figsize=(10,6))
    plt.plot(workers, times_workers, marker='o', linewidth=2, label='Фактическое время')
    plt.plot(workers, ideal, '--', marker='s', linewidth=2, label='Идеальное ускорение (1/N)')
    
    # Подписи значений для фактического времени
    for w, t in zip(workers, times_workers):
        plt.annotate(f'{t:.1f} с', xy=(w, t), xytext=(5, 5), textcoords='offset points',
                     fontsize=14, fontweight='bold')
    # Подписи для идеального времени (опционально)
    for w, t_ideal in zip(workers, ideal):
        plt.annotate(f'{t_ideal:.1f} с', xy=(w, t_ideal), xytext=(-35, -15), textcoords='offset points',
                     fontsize=14, alpha=0.7)
    
    plt.xlabel('Число асинхронных обработчиков', fontsize=14)
    plt.ylabel('Время, с', fontsize=14)
    # plt.title('Зависимость времени выполнения от числа обработчиков', fontweight='bold', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=14)
    plt.xticks(workers)
    plt.tight_layout()
    plt.savefig('graph2_scalability.png', dpi=150)
    plt.show()

# График 3: наборы XS, S, M, L – сгруппированные столбцы для трёх этапов
datasets = ['XS', 'S', 'M', 'L']
analyze_time = [0.14, 0.58, 1.04, 219.9]
generate_time = [42.29, 88.95, 71.31, 253.68]
report_time = [33.12, 53.35, 90.51, 87.39]

def plot_grouped_bars():
    x = np.arange(len(datasets))
    width = 0.25
    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width, analyze_time, width, label='Анализ структуры')
    rects2 = ax.bar(x, generate_time, width, label='Генерация тестов')
    rects3 = ax.bar(x + width, report_time, width, label='Построение отчёта')
    ax.set_xlabel('Набор функций')
    ax.set_ylabel('Время, с')
    ax.set_title('Время этапов для разных размеров проекта', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.legend()
    # Добавим значения на столбцы
    for rects in [rects1, rects2, rects3]:
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.1f}', xy=(rect.get_x() + rect.get_width()/2, height),
                        xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    plt.savefig('graph3_grouped_bars.png')
    plt.show()

# График 4: двойная ось – RSS и токены по наборам (табл.6,7)
rss = [99.35, 123.2, 176, 407.5]
tokens = [15896, 27398, 18066, 138096]

def plot_dual_axis():
    fig, ax1 = plt.subplots()
    x = np.arange(len(datasets))
    width = 0.35
    ax1.bar(x - width/2, rss, width, label='RSS (МБ)', color='tab:blue')
    ax1.set_xlabel('Набор функций')
    ax1.set_ylabel('RSS, МБ', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.set_xticks(x)
    ax1.set_xticklabels(datasets)
    
    ax2 = ax1.twinx()
    ax2.plot(x, tokens, marker='o', linewidth=2, color='tab:red', label='Число токенов')
    ax2.set_ylabel('Общее число токенов', color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')
    
    # Легенда общая
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    plt.title('Потребление памяти и токенов в зависимости от размера проекта', fontweight='bold')
    plt.tight_layout()
    plt.savefig('graph4_dual_axis.png')
    plt.show()

# График 5: глубина вложенности – токены и время (табл.9)
depth = [5, 6, 7, 8, 9]
tokens_depth = [18611, 43025, 261659, 55343, 33110]
time_depth = [116.3, 214.8, 1004.61, 198.02, 159.69]

def plot_depth_tokens_time():
    fig, ax1 = plt.subplots()
    ax1.plot(depth, tokens_depth, marker='s', linewidth=2, color='tab:green', label='Токены')
    ax1.set_xlabel('Глубина вложенности')
    ax1.set_ylabel('Число токенов', color='tab:green')
    ax1.tick_params(axis='y', labelcolor='tab:green')
    
    ax2 = ax1.twinx()
    ax2.plot(depth, time_depth, marker='o', linewidth=2, color='tab:orange', label='Время, с')
    ax2.set_ylabel('Время, с', color='tab:orange')
    ax2.tick_params(axis='y', labelcolor='tab:orange')
    
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    plt.title('Зависимость токенов и времени от глубины вложенности', fontweight='bold')
    # Отметим аномальную точку глубины 7
    ax1.annotate('Аномалия', xy=(7, 261659), xytext=(7.5, 280000),
                 arrowprops=dict(arrowstyle='->', color='red'), fontsize=9, color='red')
    plt.tight_layout()
    plt.savefig('graph5_depth_tokens_time.png')
    plt.show()

# График 6: покрытие и мутационный скор от глубины
coverage = [100, 100, 83, 80, 91.7]
mutation = [78.6, 93.75, 60, 67.85, 81.25]

def plot_depth_quality():
    plt.figure()
    plt.plot(depth, coverage, marker='^', linewidth=2, label='Покрытие, %')
    plt.plot(depth, mutation, marker='v', linewidth=2, label='Мутационный скор, %')
    plt.xlabel('Глубина вложенности')
    plt.ylabel('Процент, %')
    plt.title('Качество тестов в зависимости от глубины вложенности', fontweight='bold')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.xticks(depth)
    plt.tight_layout()
    plt.savefig('graph6_depth_quality.png')
    plt.show()

# График 7: уровни аннотированности – нормализованные метрики (табл.11)
levels = [1, 2, 3]
time_level = [629.26, 566.08, 656.17]
calls_level = [67, 62.6, 64.6]
tokens_level = [285567, 290247, 345482]

def plot_annotation_norm():
    # Нормализация относительно уровня 1
    time_norm = [t / time_level[0] for t in time_level]
    calls_norm = [c / calls_level[0] for c in calls_level]
    tokens_norm = [t / tokens_level[0] for t in tokens_level]
    
    x = np.arange(len(levels))
    width = 0.25
    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width, time_norm, width, label='Время')
    rects2 = ax.bar(x, calls_norm, width, label='LLM вызовы')
    rects3 = ax.bar(x + width, tokens_norm, width, label='Токены')
    
    ax.set_xlabel('Уровень аннотированности')
    ax.set_ylabel('Нормированное значение (уровень 1 = 1)')
    ax.set_title('Влияние аннотированности на метрики (нормализовано)', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(levels)
    ax.legend()
    
    # Добавим подписи значений
    for rects in [rects1, rects2, rects3]:
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}', xy=(rect.get_x() + rect.get_width()/2, height),
                        xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    plt.savefig('graph7_annotation_norm.png')
    plt.show()

if __name__ == "__main__":
    # Построение всех графиков
    # plot_pie()
    # plot_scalability()
    plot_grouped_bars()
    plot_dual_axis()
    plot_depth_tokens_time()
    plot_depth_quality()
    plot_annotation_norm()