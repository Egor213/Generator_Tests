Уместить все в один репозитории не удалось.

Поэтому вот тестовый репозитории с настроенным CI, где можна запускать actions и будет создавать ПР https://github.com/Egor213/Test-gen

Сам Action - https://github.com/Egor213/llm-test-generator-action

Проект генерации - https://github.com/Egor213/Generator_Tests


# Запуск приложения

КЛЮЧ МОЖНО ВЗЯТЬ В https://github.com/moevm/bsc_Muravin/blob/dev_ci/Generator_Tests/config/.env

ЛИБО СДЕЛАТЬ САМОМУ

Для локального запуска в конфиге надо установить 

```
model: <Желаемую>
base_url: "http://127.0.0.1:1234/v1" (или другой)
```



Для тестового запуска уже загружен .env и установлены параметры запуска с бесплатной моделью.
Для тестирования можно запускать файл ./start.sh или копировать оттуда команды.

Так же можно ознакомиться с содержимым ./start.sh файла

подробная информация о параметрах 
```bash
python main.py -h
```

Обычная генерация занимает время от 10 до 30 минут при небольшом количестве функции. Время можно уменьшить, если уменьшить параметры `max-fix-attempts` и `max-generate-retries`

> ⚠️ **Пример:**
> В config/config.yaml находится пример конфига
> https://github.com/Egor213/Test-gen - пример использования инструмента

## Пример конфига
```yaml
name: Auto-generate tests

on:
  pull_request:
    types: [opened, synchronize]
  workflow_dispatch:
    inputs:
      target_dir:
        description: 'Папка для генерации'
        required: false
      target_file:
        description: 'Файл'
        required: false
      target_function:
        description: 'Функция'
        required: false
      target_class:
        description: 'Класс'
        required: false

jobs:
  generate-tests:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate tests
        uses: Egor213/llm-test-generator-action@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          ai_api_key: ${{ secrets.OPENAI_API_KEY_2 }}
          project_root: 'Task_project'
          target_dir: ${{ inputs.target_dir }}
          target_file: ${{ inputs.target_file }}
          target_function: ${{ inputs.target_function }}
          target_class: ${{ inputs.target_class }}
          model: "inclusionai/ling-2.6-1t:free"
          temperature: 0.5
          max_generate_retries: 3
          max_fix_attempts: 4
          target_line_coverage: 60
          config_path: "../config/config.yaml"

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-report
          path: Task_project/test_analysis_report/
```

1. **Запустите LM Studio** и **загрузите любую локальную модель** или использовать API KEY моделей.

2. **Укажите название модели** в конфигурационном файле  
   `config/config.yaml`:
   ```yaml
   llm:
     model: "openai/gpt-oss-20b"
    ```

3. **Создате виртуальное окружение**:

   ```bash
   python -m venv venv
   ```

4. **Активируте окружение**:

   * **Windows**:

     ```bash
     venv\Scripts\activate
     ```
   * **Linux / macOS**:

     ```bash
     source venv/bin/activate
     ```

5. **Установите зависимости**:

   ```bash
   pip install -r requirements.txt
   ```

6. **Сгенерируте тесты для проекта**, указав путь до точки входа:

   ```bash
   python main.py -e "путь_до_приложения_для_которого_необходимо_сгенерировать_тесты"
   ```

   Например:

   ```bash
   python main.py -e "../Task_project/main.py"
   ```

7. Для получения дополнительной информации:

   ```bash
   python main.py -h
   ```


