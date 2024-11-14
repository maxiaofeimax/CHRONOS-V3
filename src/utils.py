from datetime import datetime



def get_current_date_and_weekday():
    """
    获取当前日期和星期
    """
    now = datetime.now()

    # 格式化日期和星期
    formatted_date = now.strftime("%Y年%m月%d日")
    # 注意：strftime中的%w返回的是数字，所以我们需要将其转换为中文的星期几
    day_of_week = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
    formatted_day_of_week = day_of_week[now.weekday()]

    # 合并日期和星期
    full_date = formatted_date + '，' + formatted_day_of_week

    return full_date


if __name__ == '__main__':
    print(get_current_date_and_weekday())