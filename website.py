from datetime import datetime

def get_index_contents():
    with open('static/index.html', 'r') as file:
        index_html_content = file.read()
        index_html_content = index_html_content.replace(
            "{{last_updated_date}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        return index_html_content