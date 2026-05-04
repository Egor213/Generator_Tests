import matplotlib.pyplot as plt

# Данные из профилирования (в секундах)
data = {
    '_build_and_generate_test_code': 90.6294,
    'refine': 417.8121,
    '_run_analysis': 107.8068,
    '_merge_and_write_results': 2.196
}
total_main = 731.2332
other = total_main - sum(data.values())  # 112.7889

# Добавляем категорию "Прочие этапы"
data['Прочие этапы'] = other

# Настройки оформления
plt.rcParams['font.size'] = 13
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['legend.fontsize'] = 12

# Цвета для каждого сектора
colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0']

# Построение круговой диаграммы
fig, ax = plt.subplots(figsize=(10, 8))
wedges, texts, autotexts = ax.pie(
    data.values(),
    labels=data.keys(),
    autopct=lambda p: f'{p:.1f}%\n({p*total_main/100:.1f}c)',
    # colors=colors,
    startangle=90,
    textprops={'fontsize': 14},
    pctdistance=0.85
)

# Увеличим шрифт для подписей процентов
for autotext in autotexts:
    autotext.set_fontsize(14)
    autotext.set_color('white')
    autotext.set_weight('bold')

# ax.set_title('Распределение времени по этапам пайплайна\n(общее время main = 731.2 с)', fontweight='bold')
plt.tight_layout()
plt.savefig('graph1_pie_updated.png', dpi=200)
plt.show()