# -*- coding: utf-8 -*-
"""
多语言文案表 —— 支持 中文 / English / 日本語 / 한국어

新增语言只需：
1) 在 LANGS 与 LANG_NAMES 里登记语言代码与显示名
2) 在 FONTS 里给一个字体候选列表
3) 在 UI / TAGS / TIPS / EXTRAS 的每一项里补齐该语言的文案
缺失的语言会回退到 FALLBACK（en），不会报错。
"""
import ctypes

LANGS = ["zh", "en", "ja", "ko"]
FALLBACK = "en"

LANG_NAMES = {
    "zh": "中文",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
}

# 各语言的首选字体（按顺序取第一个系统里存在的）
FONTS = {
    "zh": ["Microsoft YaHei UI", "微软雅黑", "Noto Sans SC", "SimHei"],
    "en": ["Segoe UI", "Microsoft YaHei UI"],
    "ja": ["Yu Gothic UI", "Meiryo UI", "MS Gothic"],
    "ko": ["Malgun Gothic", "Gulim", "Batang"],
}
MONO_FONTS = ["Consolas", "Cascadia Mono", "Lucida Console", "Courier New"]

# 主窗口约 340px、弹窗约 520px 宽（96dpi 设计稿）
UI = {
    "zh": {
        "app_name": "久坐提醒",
        "app_title": "久坐提醒 · {n} 分钟",
        "st_running": "● 计时中",
        "st_paused": "● 已暂停",
        "st_break": "● 休息中",
        "next_at": "下次提醒 {t}",
        "paused_hint": "已暂停，点“继续”恢复",
        "break_hint": "休息中，起身活动一下",
        "btn_pause": "暂停",
        "btn_resume": "继续",
        "btn_break_now": "立即休息",
        "btn_reset": "重置",
        "seated": "已坐 {n} 分钟",
        "goal": "目标 {n} 分钟",
        "stat": "今日已休息 {a} 次 · 跳过 {b} 次",
        "settings_link": "⚙ 设置",
        "break_title": "该起来活动一下了",
        "break_sub": "你已经连续坐了约 {n} 分钟",
        "step1": "第 1 步 · 喝水",
        "water_amount": "约 200 ml",
        "water_desc": "起身接一杯温水，小口慢慢喝完，别一次灌。",
        "step2": "第 2 步 · 缓解腰背 · {tag}",
        "extra": "顺便 · {name}",
        "countdown": "休息倒计时",
        "break_paused": "休息已暂停",
        "btn_done": "我已完成休息",
        "btn_snooze": "{n} 分钟后再提醒",
        "btn_skip": "跳过本次",
        "win_break": "该起来活动了",
        "win_settings": "设置",
        "set_title": "提醒设置",
        "set_sub": "保存后立即生效，并写入 config.json",
        "set_language": "界面语言",
        "set_interval": "提醒间隔",
        "set_duration": "休息时长",
        "set_snooze": "稍后提醒",
        "unit_min": "分钟",
        "set_sound": "开启提示音",
        "set_autostart": "开机自动启动",
        "autostart_hint": "开机后自动开始计时。写入当前用户注册表，不需要管理员权限。",
        "autostart_stale": "原先登记的路径已失效，重新勾选并保存即可修复。",
        "autostart_fail": "开机自启设置失败：{msg}",
        "restore": "恢复默认",
        "save": "保存",
        "cancel": "取消",
    },
    "en": {
        "app_name": "Sit Reminder",
        "app_title": "Sit Reminder · {n} min",
        "st_running": "● Running",
        "st_paused": "● Paused",
        "st_break": "● On break",
        "next_at": "Next at {t}",
        "paused_hint": "Paused — tap Resume to continue",
        "break_hint": "On break — get up and move",
        "btn_pause": "Pause",
        "btn_resume": "Resume",
        "btn_break_now": "Break now",
        "btn_reset": "Reset",
        "seated": "Sat {n} min",
        "goal": "Goal {n} min",
        "stat": "Today: {a} breaks · {b} skipped",
        "settings_link": "⚙ Settings",
        "break_title": "Time to get up",
        "break_sub": "You've been sitting for about {n} minutes",
        "step1": "Step 1 · Water",
        "water_amount": "about 200 ml",
        "water_desc": "Get up, pour a cup of warm water and sip it slowly.",
        "step2": "Step 2 · Back relief · {tag}",
        "extra": "Also · {name}",
        "countdown": "Break countdown",
        "break_paused": "Break paused",
        "btn_done": "I'm done",
        "btn_snooze": "Snooze {n} min",
        "btn_skip": "Skip",
        "win_break": "Time to move",
        "win_settings": "Settings",
        "set_title": "Settings",
        "set_sub": "Saved instantly to config.json",
        "set_language": "Language",
        "set_interval": "Interval",
        "set_duration": "Break",
        "set_snooze": "Snooze",
        "unit_min": "min",
        "set_sound": "Play sound",
        "set_autostart": "Start with Windows",
        "autostart_hint": "Starts automatically at logon. Writes to the "
                          "current-user registry — no admin rights needed.",
        "autostart_stale": "The registered path is broken. Tick and save to "
                           "repair it.",
        "autostart_fail": "Could not set auto start: {msg}",
        "restore": "Reset defaults",
        "save": "Save",
        "cancel": "Cancel",
    },
    "ja": {
        "app_name": "座りすぎ注意",
        "app_title": "座りすぎ注意 · {n}分",
        "st_running": "● 計測中",
        "st_paused": "● 一時停止",
        "st_break": "● 休憩中",
        "next_at": "次の通知 {t}",
        "paused_hint": "一時停止中。「再開」で戻ります",
        "break_hint": "休憩中。立って動きましょう",
        "btn_pause": "一時停止",
        "btn_resume": "再開",
        "btn_break_now": "今すぐ休憩",
        "btn_reset": "リセット",
        "seated": "着席 {n} 分",
        "goal": "目標 {n} 分",
        "stat": "本日 {a} 回休憩 · {b} 回スキップ",
        "settings_link": "⚙ 設定",
        "break_title": "そろそろ立ちましょう",
        "break_sub": "約 {n} 分続けて座っています",
        "step1": "ステップ 1 · 水分",
        "water_amount": "約 200 ml",
        "water_desc": "立って温かい水を一杯。少しずつ飲みましょう。",
        "step2": "ステップ 2 · 腰背ケア · {tag}",
        "extra": "ついでに · {name}",
        "countdown": "休憩の残り",
        "break_paused": "休憩を一時停止中",
        "btn_done": "休憩終了",
        "btn_snooze": "{n} 分後に通知",
        "btn_skip": "スキップ",
        "win_break": "休憩の時間です",
        "win_settings": "設定",
        "set_title": "設定",
        "set_sub": "保存すると即時反映され、config.json に書き込まれます",
        "set_language": "表示言語",
        "set_interval": "通知間隔",
        "set_duration": "休憩時間",
        "set_snooze": "スヌーズ",
        "unit_min": "分",
        "set_sound": "通知音を鳴らす",
        "set_autostart": "Windows 起動時に開始",
        "autostart_hint": "ログオン時に自動起動します。現在のユーザーの"
                          "レジストリに書き込むため、管理者権限は不要です。",
        "autostart_stale": "登録されたパスが無効です。チェックして保存すると修復されます。",
        "autostart_fail": "自動起動の設定に失敗しました：{msg}",
        "restore": "初期値に戻す",
        "save": "保存",
        "cancel": "キャンセル",
    },
    "ko": {
        "app_name": "앉아있기 알림",
        "app_title": "앉아있기 알림 · {n}분",
        "st_running": "● 작동 중",
        "st_paused": "● 일시정지",
        "st_break": "● 휴식 중",
        "next_at": "다음 알림 {t}",
        "paused_hint": "일시정지됨 — '재개'를 누르세요",
        "break_hint": "휴식 중 — 일어나서 움직이세요",
        "btn_pause": "일시정지",
        "btn_resume": "재개",
        "btn_break_now": "지금 휴식",
        "btn_reset": "초기화",
        "seated": "{n}분 앉음",
        "goal": "목표 {n}분",
        "stat": "오늘 {a}회 휴식 · {b}회 건너뜀",
        "settings_link": "⚙ 설정",
        "break_title": "일어날 시간이에요",
        "break_sub": "약 {n}분째 앉아 있었어요",
        "step1": "1단계 · 물 마시기",
        "water_amount": "약 200 ml",
        "water_desc": "일어나서 따뜻한 물 한 잔을 천천히 나눠 마시세요.",
        "step2": "2단계 · 허리 케어 · {tag}",
        "extra": "겸사겸사 · {name}",
        "countdown": "휴식 남은 시간",
        "break_paused": "휴식 일시정지됨",
        "btn_done": "휴식 완료",
        "btn_snooze": "{n}분 뒤 알림",
        "btn_skip": "건너뛰기",
        "win_break": "움직일 시간",
        "win_settings": "설정",
        "set_title": "설정",
        "set_sub": "저장하면 즉시 적용되고 config.json에 기록됩니다",
        "set_language": "언어",
        "set_interval": "알림 간격",
        "set_duration": "휴식 시간",
        "set_snooze": "다시 알림",
        "unit_min": "분",
        "set_sound": "알림음 재생",
        "set_autostart": "Windows 시작 시 실행",
        "autostart_hint": "로그온하면 자동으로 시작됩니다. 현재 사용자 레지스트리에 "
                          "기록하므로 관리자 권한이 필요 없습니다.",
        "autostart_stale": "등록된 경로가 유효하지 않습니다. 체크하고 저장하면 복구됩니다.",
        "autostart_fail": "자동 시작 설정 실패: {msg}",
        "restore": "기본값 복원",
        "save": "저장",
        "cancel": "취소",
    },
}

TAGS = {
    "back": {"zh": "腰部", "en": "lower back", "ja": "腰", "ko": "허리"},
    "side": {"zh": "腰侧", "en": "waist", "ja": "体側", "ko": "옆구리"},
    "neck": {"zh": "颈肩", "en": "neck & shoulders", "ja": "首・肩", "ko": "목·어깨"},
    "circulation": {"zh": "循环", "en": "circulation", "ja": "血行", "ko": "혈액순환"},
    "eyes": {"zh": "眼睛", "en": "eyes", "ja": "目", "ko": "눈"},
    "breath": {"zh": "呼吸", "en": "breathing", "ja": "呼吸", "ko": "호흡"},
}

# 主动作库：每个动作给出 (名称, 做法) 四种语言
TIPS = {
    "back_extension": {
        "tag": "back",
        "zh": ("站姿后仰伸展", "双手扶住后腰，缓慢向后仰，到有轻微牵拉感停住，保持 10 秒，做 3 次。"),
        "en": ("Standing back extension", "Hands on your lower back, arch backwards slowly until you feel a light stretch. Hold 10 s, repeat 3×."),
        "ja": ("立ったまま上体反らし", "両手を腰に当て、軽く張りを感じるところまでゆっくり上体を反らす。10秒キープ×3回。"),
        "ko": ("서서 허리 젖히기", "양손을 허리에 대고 가볍게 당김이 느껴질 때까지 천천히 상체를 젖힙니다. 10초 유지 × 3회."),
    },
    "cat_cow": {
        "tag": "back",
        "zh": ("猫牛式", "双手双膝撑地，吸气塌腰抬头，呼气拱背低头，缓慢做 8~10 次。"),
        "en": ("Cat–cow", "On hands and knees, inhale and drop your belly while lifting your head; exhale and round your back. 8–10 slow reps."),
        "ja": ("キャット&カウ", "四つ這いで、吸気に腰を落として顔を上げ、呼気に背中を丸めて頭を下げる。ゆっくり8〜10回。"),
        "ko": ("캣-카우", "네 발로 기어 자세에서 숨을 들이쉬며 허리를 내리고 고개를 들고, 내쉬며 등을 둥글게 말아 고개를 숙입니다. 천천히 8~10회."),
    },
    "child_pose": {
        "tag": "back",
        "zh": ("婴儿式放松", "跪坐，上身向前趴下、手臂前伸，额头贴地，深呼吸 30 秒。"),
        "en": ("Child's pose", "Kneel, fold forward with arms stretched out and forehead down. Breathe deeply for 30 s."),
        "ja": ("チャイルドポーズ", "正座から上体を前に倒し、両腕を前に伸ばして額をつける。30秒深く呼吸。"),
        "ko": ("아기 자세", "무릎을 꿇고 상체를 앞으로 숙여 팔을 뻗고 이마를 바닥에 댑니다. 30초 깊게 호흡."),
    },
    "glute_bridge": {
        "tag": "back",
        "zh": ("臀桥", "仰卧屈膝，臀部抬起使肩—髋—膝成一条直线，保持 20 秒，做 3 组。"),
        "en": ("Glute bridge", "Lie on your back, knees bent, lift your hips until shoulder–hip–knee form a line. Hold 20 s, 3 sets."),
        "ja": ("ヒップリフト", "仰向けで膝を立て、肩・腰・膝が一直線になるまでお尻を上げる。20秒キープ×3セット。"),
        "ko": ("힙 브리지", "누워서 무릎을 세우고 어깨-엉덩이-무릎이 일직선이 되게 엉덩이를 들어 올립니다. 20초 유지 × 3세트."),
    },
    "wall_stand": {
        "tag": "back",
        "zh": ("靠墙站立", "后脑、肩胛、臀部、小腿贴墙站 1 分钟，收下巴，让腰背回到中立位。"),
        "en": ("Wall stand", "Stand with the back of your head, shoulder blades, hips and calves against a wall for 1 min. Chin tucked."),
        "ja": ("壁立ち", "後頭部・肩甲骨・お尻・ふくらはぎを壁につけて1分立つ。あごを引いて腰背を中立に戻す。"),
        "ko": ("벽에 기대 서기", "뒤통수, 견갑골, 엉덩이, 종아리를 벽에 붙이고 1분 섭니다. 턱을 당겨 허리를 중립으로 되돌립니다."),
    },
    "hip_flexor": {
        "tag": "back",
        "zh": ("髋屈肌拉伸", "弓箭步，后腿膝盖贴地，重心缓慢前移，每侧保持 20 秒。"),
        "en": ("Hip flexor stretch", "Kneel in a lunge, back knee on the floor, shift your weight slowly forward. Hold 20 s each side."),
        "ja": ("腸腰筋ストレッチ", "片膝をついたランジ姿勢で、後ろ脚の膝を床につけ、体重をゆっくり前へ。左右20秒ずつ。"),
        "ko": ("장요근 스트레칭", "한쪽 무릎을 바닥에 대고 런지 자세를 잡은 뒤 체중을 천천히 앞으로 옮깁니다. 좌우 20초씩."),
    },
    "side_bend": {
        "tag": "side",
        "zh": ("侧腰拉伸", "站立，右手上举向左侧屈，感受右侧腰腹拉开，保持 15 秒后换边。"),
        "en": ("Side bend", "Stand tall, reach your right arm up and lean left. Feel the right side open. Hold 15 s, then switch."),
        "ja": ("体側伸ばし", "立って右手を上げ、体を左に倒す。右側が伸びるのを感じて15秒キープ、左右交代。"),
        "ko": ("옆구리 스트레칭", "바르게 서서 오른팔을 들어 왼쪽으로 기울입니다. 오른쪽 옆구리가 늘어나는 느낌으로 15초 유지 후 교대."),
    },
    "seated_twist": {
        "tag": "side",
        "zh": ("坐姿转体", "坐直，右手扶左膝，身体向左后方转，保持 15 秒，左右各 2 次。"),
        "en": ("Seated twist", "Sit tall, right hand on left knee, rotate your torso to the left. Hold 15 s, twice each side."),
        "ja": ("座位ツイスト", "背筋を伸ばして座り、右手を左膝に当てて上体を左後ろへねじる。15秒キープ、左右2回ずつ。"),
        "ko": ("앉아서 비틀기", "허리를 펴고 앉아 오른손을 왼무릎에 대고 상체를 왼쪽 뒤로 돌립니다. 15초 유지, 좌우 2회씩."),
    },
    "neck_clock": {
        "tag": "neck",
        "zh": ("颈部米字操", "头部缓慢按“米”字轨迹画两圈，动作要慢，不要猛甩。"),
        "en": ("Neck range of motion", "Slowly trace two wide circles with your head. Keep it gentle — never jerk or force it."),
        "ja": ("首の可動域運動", "頭で大きく円を2回ゆっくり描く。急な動きや勢いはつけないこと。"),
        "ko": ("목 가동 범위 운동", "고개로 큰 원을 천천히 두 바퀴 그립니다. 절대 빠르게 휘두르지 마세요."),
    },
    "scapula_squeeze": {
        "tag": "neck",
        "zh": ("肩胛骨后收", "双肩下沉，肩胛骨向后向下夹紧 5 秒再放松，做 10 次。"),
        "en": ("Scapular squeeze", "Drop your shoulders, squeeze the shoulder blades back and down for 5 s, release. 10 reps."),
        "ja": ("肩甲骨寄せ", "肩を下げ、肩甲骨を後ろ下方向に5秒寄せて緩める。10回。"),
        "ko": ("견갑골 모으기", "어깨를 내리고 견갑골을 뒤아래로 5초 모았다가 풉니다. 10회."),
    },
    "chest_open": {
        "tag": "neck",
        "zh": ("扩胸开肩", "双手在背后交握、向后上方抬起，胸口打开，保持 15 秒。"),
        "en": ("Chest opener", "Clasp your hands behind your back, lift them up and back, open the chest. Hold 15 s."),
        "ja": ("胸開き", "背中で両手を組み、後ろ上方へ上げて胸を開く。15秒キープ。"),
        "ko": ("가슴 열기", "등 뒤에서 양손을 깍지 끼고 위뒤로 들어 가슴을 폅니다. 15초 유지."),
    },
    "brisk_walk": {
        "tag": "circulation",
        "zh": ("起身快走", "离开座位快走 2 分钟，双臂自然摆动，促进下肢血液回流。"),
        "en": ("Brisk walk", "Leave your desk and walk briskly for 2 minutes, swinging your arms naturally."),
        "ja": ("早歩き", "席を立って2分間早歩き。腕を自然に振って下肢の血流を促す。"),
        "ko": ("빠르게 걷기", "자리에서 일어나 2분간 빠르게 걷습니다. 팔을 자연스럽게 흔들어 다리 혈액순환을 돕습니다."),
    },
    "calf_pump": {
        "tag": "circulation",
        "zh": ("踮脚泵血", "扶住桌沿，踮起脚尖再落下，做 20 次，缓解小腿发胀。"),
        "en": ("Calf raises", "Hold the desk edge and rise onto your toes, then lower. 20 reps to ease stiff calves."),
        "ja": ("かかと上げ", "机に手を添えて、かかとを上げ下げする。20回でふくらはぎの重さを解消。"),
        "ko": ("발뒤꿈치 들기", "책상을 짚고 발뒤꿈치를 들었다 내립니다. 20회로 종아리 뭉침을 완화."),
    },
}

TIP_ORDER = ["back_extension", "cat_cow", "child_pose", "glute_bridge", "wall_stand",
             "hip_flexor", "side_bend", "seated_twist", "neck_clock",
             "scapula_squeeze", "chest_open", "brisk_walk", "calf_pump"]

# 「顺便」小提示（不会与主动作重名）
EXTRAS = {
    "eyes_20": {
        "zh": ("20-20-20 远眺", "看向 20 米外的远处 20 秒，多眨眼，让睫状肌放松。"),
        "en": ("20-20-20 rule", "Look at something 20 metres away for 20 s and blink often to relax your eyes."),
        "ja": ("20-20-20 ルール", "20メートル先を20秒見て、まばたきを多く。毛様体筋をゆるめる。"),
        "ko": ("20-20-20 규칙", "20m 떨어진 곳을 20초 바라보고 자주 눈을 깜빡여 눈의 피로를 풉니다."),
    },
    "breath_478": {
        "zh": ("4-7-8 深呼吸", "吸气 4 秒、屏息 7 秒、缓慢呼气 8 秒，做 4 轮，放松肩颈。"),
        "en": ("4-7-8 breathing", "Inhale 4 s, hold 7 s, exhale slowly for 8 s. Four rounds to release your shoulders."),
        "ja": ("4-7-8 呼吸", "4秒吸って、7秒止めて、8秒かけてゆっくり吐く。4セットで肩首がゆるむ。"),
        "ko": ("4-7-8 호흡", "4초 들이쉬고 7초 멈추고 8초에 걸쳐 천천히 내쉽니다. 4세트로 어깨와 목을 이완."),
    },
    "chin_tuck": {
        "zh": ("收下巴", "下巴水平向后收，像挤双下巴，保持 5 秒，做 8 次。"),
        "en": ("Chin tuck", "Draw your chin straight back as if making a double chin. Hold 5 s, 8 reps."),
        "ja": ("あご引く", "あごを水平に後ろへ引いて二重あごを作る感じで5秒キープ。8回。"),
        "ko": ("턱 당기기", "턱을 수평으로 뒤로 당겨 이중턱을 만드는 느낌으로 5초 유지. 8회."),
    },
    "ankle_circle": {
        "zh": ("转动脚踝", "双脚离地，脚踝顺时针、逆时针各转 10 圈，预防下肢肿胀。"),
        "en": ("Ankle circles", "Lift your feet and circle each ankle 10 times both ways to prevent swelling."),
        "ja": ("足首回し", "両足を浮かせ、足首を時計回り・反時計回りに各10回。むくみ予防。"),
        "ko": ("발목 돌리기", "발을 들고 발목을 시계·반시계 방향으로 각 10회 돌립니다. 부종 예방."),
    },
}

EXTRA_ORDER = ["eyes_20", "breath_478", "chin_tuck", "ankle_circle"]


def normalize_lang(code):
    """把任意输入收敛到受支持的语言代码"""
    if not code:
        return FALLBACK
    code = str(code).strip().lower().replace("_", "-")
    for sep in ("-",):
        head = code.split(sep)[0]
        if head in LANGS:
            return head
    return code if code in LANGS else FALLBACK


def detect_lang():
    """按 Windows 界面语言猜一个默认语言，猜不出就用中文"""
    try:
        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        primary = langid & 0x3FF
        table = {0x04: "zh", 0x09: "en", 0x11: "ja", 0x12: "ko"}
        return table.get(primary, "zh")
    except Exception:
        return "zh"


def text(lang, key, **kw):
    """取一条 UI 文案，缺失则回退到 FALLBACK"""
    lang = normalize_lang(lang)
    table = UI.get(lang) or {}
    s = table.get(key)
    if s is None:
        s = UI[FALLBACK].get(key, key)
    if kw:
        try:
            return s.format(**kw)
        except Exception:
            return s
    return s


def tag_text(lang, tag):
    lang = normalize_lang(lang)
    d = TAGS.get(tag, {})
    return d.get(lang) or d.get(FALLBACK) or tag


def tip_text(lang, tid):
    """-> (名称, 做法)"""
    lang = normalize_lang(lang)
    d = TIPS.get(tid, {})
    pair = d.get(lang) or d.get(FALLBACK)
    return pair if pair else (tid, "")


def extra_text(lang, eid):
    """-> (名称, 做法)"""
    lang = normalize_lang(lang)
    d = EXTRAS.get(eid, {})
    pair = d.get(lang) or d.get(FALLBACK)
    return pair if pair else (eid, "")


def pick_font(lang, available=None):
    """挑一个系统里真实存在的字体"""
    lang = normalize_lang(lang)
    cands = list(FONTS.get(lang) or []) + list(FONTS[FALLBACK])
    if available is None:
        return cands[0]
    for c in cands:
        if c in available:
            return c
    return FONTS[FALLBACK][0]
