"""
GM打卡日志
GM Check-in Tracker - 每天GM，养成习惯！

Copyright (c) 2025 ZYER
All rights reserved.

Author: ZYER
GitHub: https://github.com/zyerai
"""

import sqlite3
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gm-checkin-secret-key'
DATABASE = 'gm_tracker.db'


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库"""
    conn = get_db()
    cursor = conn.cursor()

    # 打卡记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checkin_date DATE NOT NULL UNIQUE,
            mood TEXT DEFAULT 'gm',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


def get_streak():
    """获取当前连续打卡天数"""
    conn = get_db()
    cursor = conn.cursor()

    today = date.today()
    streak = 0
    check_date = today

    while True:
        cursor.execute('SELECT * FROM checkins WHERE checkin_date = ?', (check_date,))
        if cursor.fetchone():
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    conn.close()
    return streak


def get_month_checkins(year, month):
    """获取指定月份的所有打卡记录"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT checkin_date, mood, notes
        FROM checkins
        WHERE strftime('%Y', checkin_date) = ? AND strftime('%m', checkin_date) = ?
        ORDER BY checkin_date
    ''', (str(year), f'{month:02d}'))

    checkins = cursor.fetchall()
    conn.close()

    return {row['checkin_date']: row for row in checkins}


@app.context_processor
def utility_processor():
    """模板工具函数"""
    def format_date(date_str):
        if not date_str:
            return ''
        try:
            dt = datetime.fromisoformat(str(date_str))
            return dt.strftime('%Y-%m-%d')
        except:
            return str(date_str)

    def mood_emoji(mood):
        """心情对应的emoji"""
        mood_map = {
            'gm': '🌅',
            'bullish': '🚀',
            'focused': '💪',
            'learning': '📚',
            'chill': '😌',
            'grinding': '⚡'
        }
        return mood_map.get(mood, '🌅')

    return dict(format_date=format_date, mood_emoji=mood_emoji)


# ==================== 路由 ====================

@app.route('/')
def index():
    """首页 - 日历视图"""
    today = date.today()

    # 获取当前月份
    year = int(request.args.get('year', today.year))
    month = int(request.args.get('month', today.month))

    # 获取打卡记录
    checkins = get_month_checkins(year, month)

    # 获取连续打卡天数
    streak = get_streak()

    # 获取总打卡天数
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM checkins')
    total_checkins = cursor.fetchone()['total']
    conn.close()

    # 生成日历数据
    import calendar
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    month_name = calendar.month_name[month]

    # 计算上个月和下个月
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    return render_template('index.html',
                          year=year,
                          month=month,
                          month_name=month_name,
                          month_days=month_days,
                          checkins=checkins,
                          streak=streak,
                          total_checkins=total_checkins,
                          today=today,
                          prev_year=prev_year,
                          prev_month=prev_month,
                          next_year=next_year,
                          next_month=next_month)


@app.route('/checkin', methods=['POST'])
def checkin():
    """打卡"""
    checkin_date = request.form.get('checkin_date', str(date.today()))
    mood = request.form.get('mood', 'gm')
    notes = request.form.get('notes', '')

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO checkins (checkin_date, mood, notes)
            VALUES (?, ?, ?)
        ''', (checkin_date, mood, notes))
        conn.commit()
    except sqlite3.IntegrityError:
        # 已打卡，更新记录
        cursor.execute('''
            UPDATE checkins SET mood=?, notes=?
            WHERE checkin_date=?
        ''', (mood, notes, checkin_date))
        conn.commit()

    conn.close()
    return redirect(url_for('index'))


@app.route('/delete/<checkin_date>', methods=['POST'])
def delete_checkin(checkin_date):
    """删除打卡记录"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM checkins WHERE checkin_date = ?', (checkin_date,))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))


@app.route('/generate_gm')
def generate_gm():
    """生成GM文案"""
    import random

    gm_templates = [
        "GM! {date} {mood} 🌅",
        "Good Morning! {date} {mood} 让我们开始新的一天！",
        "GM GM GM! {date} {mood} WAGMI 💪",
        "GM! {date} {mood} 今天也要加油！",
        "早安！{date} {mood} 新的一天，新的机会！",
        "GM! {date} {mood} 定投继续，学习继续！",
        "Good Morning! {date} {mood} 坚持就是胜利！",
    ]

    moods = {
        "gm": "🌅",
        "bullish": "🚀🚀🚀",
        "focused": "💪",
        "learning": "📚",
        "chill": "😌",
        "grinding": "⚡"
    }

    mood = request.args.get('mood', 'gm')
    today = date.today()

    template = random.choice(gm_templates)
    gm_text = template.format(
        date=today.strftime('%Y-%m-%d'),
        mood=moods.get(mood, '🌅')
    )

    return jsonify({'gm_text': gm_text})


@app.route('/history')
def history():
    """历史记录"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT checkin_date, mood, notes
        FROM checkins
        ORDER BY checkin_date DESC
        LIMIT 100
    ''')
    history = cursor.fetchall()

    conn.close()
    return render_template('history.html', history=history)


@app.route('/stats')
def stats():
    """统计页面"""
    conn = get_db()
    cursor = conn.cursor()

    # 总打卡天数
    cursor.execute('SELECT COUNT(*) as total FROM checkins')
    total_checkins = cursor.fetchone()['total']

    # 当前连续打卡天数
    streak = get_streak()

    # 最长连续打卡天数（简化版本）
    cursor.execute('SELECT COUNT(*) as total FROM checkins')
    total_checkins_for_max = cursor.fetchone()['total']
    max_streak = total_checkins_for_max  # 暂时使用总数作为最长连续

    # 按心情统计
    cursor.execute('''
        SELECT mood, COUNT(*) as count
        FROM checkins
        GROUP BY mood
        ORDER BY count DESC
    ''')
    by_mood = cursor.fetchall()

    # 本月打卡天数
    today = date.today()
    cursor.execute('''
        SELECT COUNT(*) as this_month
        FROM checkins
        WHERE strftime('%Y', checkin_date) = ? AND strftime('%m', checkin_date) = ?
    ''', (str(today.year), f'{today.month:02d}'))
    this_month = cursor.fetchone()['this_month']

    # 获取所有打卡日期（用于生成图表数据）
    cursor.execute('SELECT checkin_date FROM checkins ORDER BY checkin_date')
    all_checkins = [row['checkin_date'] for row in cursor.fetchall()]

    conn.close()

    # 计算打卡率（过去30天）
    thirty_days_ago = today - timedelta(days=30)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) as count
        FROM checkins
        WHERE checkin_date >= ?
    ''', (str(thirty_days_ago),))
    last_30_days = cursor.fetchone()['count']
    checkin_rate = (last_30_days / 30) * 100

    return render_template('stats.html',
                          total_checkins=total_checkins,
                          streak=streak,
                          max_streak=max_streak,
                          by_mood=by_mood,
                          this_month=this_month,
                          checkin_rate=checkin_rate,
                          all_checkins=all_checkins)


if __name__ == '__main__':
    # 初始化数据库
    init_db()
    print("=" * 60)
    print("GM打卡日志启动成功！")
    print("访问地址: http://localhost:5001")
    print("每天GM，养成习惯！")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5001)
