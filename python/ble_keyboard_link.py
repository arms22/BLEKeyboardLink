from pynput import mouse
import keyboard
import serial
import struct
import sys
import threading
from collections import defaultdict
import time
import argparse

# ArgumentParserオブジェクトの作成
parser = argparse.ArgumentParser(description='Send PC keyboard and mouse input via nRF52840 device to other devices.')

# オプションの定義
parser.add_argument('--screen_width', type=int, default=1920, help='Width of the screen')
parser.add_argument('--screen_height', type=int, default=1080, help='Height of the screen')
parser.add_argument('--display_scale', type=float, default=1, help='Display scale for screen')
parser.add_argument('port', type=str, help='COM port')

args = parser.parse_args()

ser = serial.Serial(port=args.port, baudrate=115200, timeout=1)
lock = threading.Lock()

mouse_buttons = 0
display_scale = args.display_scale
center_x = args.screen_width / 2
center_y = args.screen_height / 2
mouse_x = center_x
mouse_y = center_y
mouse_skip_n = 1
mouse_set_req = False
cond = threading.Condition()

def send_mouse(buttons, dx, dy, wheel):
    event_data = struct.pack('BBbbbBBB', 0x5e, buttons, dx, dy, wheel, 0, 0, 0)
    # print('Send', event_data)
    with lock:
        ser.write(event_data)

def update_mouse_xy(x, y):
    global mouse_x
    global mouse_y
    # x = min(max(x, 0),1920)
    # y = min(max(y, 0),1080)
    mx = int(x - mouse_x)
    my = int(y - mouse_y)
    mouse_x = x
    mouse_y = y
    return max(min(mx, 127),-128), max(min(my, 127),-128)

def move(x, y):
    with cond:
        # positionで指定した表示座標が1回入ってくるので無視する
        global mouse_skip_n
        global mouse_set_req
        if mouse_skip_n:
            mouse_skip_n -= 1
            print('set', x, y)
            if mouse_skip_n == 0:
                update_mouse_xy(x, y)
            return
        mx, my = update_mouse_xy(x, y)
        print('move', x, y, mx, my)
        if mx or my:
            send_mouse(mouse_buttons, mx, my, 0)
        # ここでposition設定すると動きがおかしくなるのでメインループでposition設定する
        if abs(x - center_x) > center_x*0.95 or abs(y - center_y) > center_y*0.95:
            mouse_set_req = True
            cond.notify_all()

def click(x, y, button, pressed):
    global mouse_buttons
    btn_to_hid_button = {
        mouse.Button.left: 1<<0,
        mouse.Button.right: 1<<1,
        mouse.Button.middle: 1<<2,
        mouse.Button.x1: 1<<3,
        mouse.Button.x2: 1<<4,
    }
    if pressed:
        mouse_buttons |= btn_to_hid_button[button]
    else:
        mouse_buttons ^= btn_to_hid_button[button]
    mx, my = update_mouse_xy(x, y)
    print('click', mouse_buttons, mx, my)
    send_mouse(mouse_buttons, mx, my, 0)

def scroll(x, y, dx, dy):
    mx, my = update_mouse_xy(x, y)
    print('wheel', dx, dy, mx, my)
    send_mouse(mouse_buttons, mx, my, dy)

mouse_controller = mouse.Controller()
mouse_controller.position = (center_x / display_scale, center_y / display_scale)

mouse_listener = mouse.Listener(
    on_move=move,
    on_click=click,
    on_scroll=scroll)
mouse_listener.start()

modifier = 0
keycode = set()

event_name_to_modifier = defaultdict(int, {
    'ctrl':1<<0,
    'shift':1<<1,
    'alt':1<<2,
    'left windows':1<<3,
    'right ctrl':1<<4,
    'right shift':1<<5,
    'right alt':1<<6,
    'right windows':1<<7,
})

# 参考
# https://bsakatu.net/doc/usb-hid-to-scancode/

scan_code_to_hid_key_code = defaultdict(int, {
# 0:0x00, # HID_KEY_NONE
0x1E:0x04, # HID_KEY_A
0x30:0x05, # HID_KEY_B
0x2E:0x06, # HID_KEY_C
0x20:0x07, # HID_KEY_D
0x12:0x08, # HID_KEY_E
0x21:0x09, # HID_KEY_F
0x22:0x0A, # HID_KEY_G
0x23:0x0B, # HID_KEY_H
0x17:0x0C, # HID_KEY_I
0x24:0x0D, # HID_KEY_J
0x25:0x0E, # HID_KEY_K
0x26:0x0F, # HID_KEY_L
0x32:0x10, # HID_KEY_M
0x31:0x11, # HID_KEY_N
0x18:0x12, # HID_KEY_O
0x19:0x13, # HID_KEY_P
0x10:0x14, # HID_KEY_Q
0x13:0x15, # HID_KEY_R
0x1F:0x16, # HID_KEY_S
0x14:0x17, # HID_KEY_T
0x16:0x18, # HID_KEY_U
0x2F:0x19, # HID_KEY_V
0x11:0x1A, # HID_KEY_W
0x2D:0x1B, # HID_KEY_X
0x15:0x1C, # HID_KEY_Y
# 0x2C:00 # HID_KEY_Z
0x02:0x1E, # HID_KEY_1
0x03:0x1F, # HID_KEY_2
0x04:0x20, # HID_KEY_3
0x05:0x21, # HID_KEY_4
0x06:0x22, # HID_KEY_5
0x07:0x23, # HID_KEY_6
0x08:0x24, # HID_KEY_7
0x09:0x25, # HID_KEY_8
0x0A:0x26, # HID_KEY_9
0x0B:0x27, # HID_KEY_0
0x1C:0x28, # HID_KEY_ENTER
0x01:0x29, # HID_KEY_ESCAPE
0x0E:0x2A, # HID_KEY_BACKSPACE
0x0F:0x2B, # HID_KEY_TAB
0x39:0x2C, # HID_KEY_SPACE
0x0C:0x2D, # HID_KEY_MINUS
0x0D:0x2E, # HID_KEY_EQUAL
0x1A:0x2F, # HID_KEY_BRACKET_LEFT
0x1B:0x30, # HID_KEY_BRACKET_RIGHT
0x2B:0x31, # HID_KEY_BACKSLASH
# 0x0:0x32, # HID_KEY_EUROPE_1 ??
0x27:0x33, # HID_KEY_SEMICOLON
0x28:0x34, # HID_KEY_APOSTROPHE
0x29:0x35, # HID_KEY_GRAVE
0x33:0x36, # HID_KEY_COMMA
0x34:0x37, # HID_KEY_PERIOD
0x35:0x38, # HID_KEY_SLASH ??
0x3A:0x39, # HID_KEY_CAPS_LOCK
0x3b:0x3A, # HID_KEY_F1
0x3c:0x3B, # HID_KEY_F2
0x3d:0x3C, # HID_KEY_F3
0x3e:0x3D, # HID_KEY_F4
0x3f:0x3E, # HID_KEY_F5
0x40:0x3F, # HID_KEY_F6
0x41:0x40, # HID_KEY_F7
0x42:0x41, # HID_KEY_F8
0x43:0x42, # HID_KEY_F9
0x44:0x43, # HID_KEY_F10
0x57:0x44, # HID_KEY_F11
0x58:0x45, # HID_KEY_F12
# 0:0x46, # HID_KEY_PRINT_SCREEN ??
0x46:0x47, # HID_KEY_SCROLL_LOCK
# 0:0x48, # HID_KEY_PAUSE ??
0x52:0x49, # HID_KEY_INSERT
0x47:0x4A, # HID_KEY_HOME
0x49:0x4B, # HID_KEY_PAGE_UP
0x53:0x4C, # HID_KEY_DELETE
0x4F:0x4D, # HID_KEY_END
0x51:0x4E, # HID_KEY_PAGE_DOWN
0x4D:0x4F, # HID_KEY_ARROW_RIGHT
0x4B:0x50, # HID_KEY_ARROW_LEFT
0x50:0x51, # HID_KEY_ARROW_DOWN
0x48:0x52, # HID_KEY_ARROW_UP
0x45:0x53, # HID_KEY_NUM_LOCK
# 0:0x54, # HID_KEY_KEYPAD_DIVIDE
# 0:0x55, # HID_KEY_KEYPAD_MULTIPLY
# 0:0x56, # HID_KEY_KEYPAD_SUBTRACT
# 0:0x57, # HID_KEY_KEYPAD_ADD
# 0:0x58, # HID_KEY_KEYPAD_ENTER
# 0:0x59, # HID_KEY_KEYPAD_1
# 0:0x5A, # HID_KEY_KEYPAD_2
# 0:0x5B, # HID_KEY_KEYPAD_3
# 0:0x5C, # HID_KEY_KEYPAD_4
# 0:0x5D, # HID_KEY_KEYPAD_5
# 0:0x5E, # HID_KEY_KEYPAD_6
# 0:0x5F, # HID_KEY_KEYPAD_7
# 0:0x60, # HID_KEY_KEYPAD_8
# 0:0x61, # HID_KEY_KEYPAD_9
# 0:0x62, # HID_KEY_KEYPAD_0
# 0:0x63, # HID_KEY_KEYPAD_DECIMAL
# 0:0x64, # HID_KEY_EUROPE_2
# 0:0x65, # HID_KEY_APPLICATION
# 0:0x66, # HID_KEY_POWER
# 0:0x67, # HID_KEY_KEYPAD_EQUAL
# 0:0x68, # HID_KEY_F13
# 0:0x69, # HID_KEY_F14
# 0:0x6A, # HID_KEY_F15
# 0:0x6B, # HID_KEY_F16
# 0:0x6C, # HID_KEY_F17
# 0:0x6D, # HID_KEY_F18
# 0:0x6E, # HID_KEY_F19
# 0:0x6F, # HID_KEY_F20
# 0:0x70, # HID_KEY_F21
# 0:0x71, # HID_KEY_F22
# 0:0x72, # HID_KEY_F23
# 0:0x73, # HID_KEY_F24
# 0:0x74, # HID_KEY_EXECUTE
# 0:0x75, # HID_KEY_HELP
# 0:0x76, # HID_KEY_MENU
# 0:0x77, # HID_KEY_SELECT
# 0:0x78, # HID_KEY_STOP
# 0:0x79, # HID_KEY_AGAIN
# 0:0x7A, # HID_KEY_UNDO
# 0:0x7B, # HID_KEY_CUT
# 0:0x7C, # HID_KEY_COPY
# 0:0x7D, # HID_KEY_PASTE
# 0:0x7E, # HID_KEY_FIND
# 0:0x7F, # HID_KEY_MUTE
# 0:0x80, # HID_KEY_VOLUME_UP
# 0:0x81, # HID_KEY_VOLUME_DOWN
# 0:0x82, # HID_KEY_LOCKING_CAPS_LOCK
# 0:0x83, # HID_KEY_LOCKING_NUM_LOCK
# 0:0x84, # HID_KEY_LOCKING_SCROLL_LOCK
# 0:0x85, # HID_KEY_KEYPAD_COMMA
# 0:0x86, # HID_KEY_KEYPAD_EQUAL_SIGN
# 0:0x87, # HID_KEY_KANJI1
# 0:0x88, # HID_KEY_KANJI2
# 0:0x89, # HID_KEY_KANJI3
# 0:0x8A, # HID_KEY_KANJI4
# 0:0x8B, # HID_KEY_KANJI5
# 0:0x8C, # HID_KEY_KANJI6
# 0:0x8D, # HID_KEY_KANJI7
# 0:0x8E, # HID_KEY_KANJI8
# 0:0x8F, # HID_KEY_KANJI9
# 0:0x90, # HID_KEY_LANG1
# 0:0x91, # HID_KEY_LANG2
# 0:0x92, # HID_KEY_LANG3
# 0:0x93, # HID_KEY_LANG4
# 0:0x94, # HID_KEY_LANG5
# 0:0x95, # HID_KEY_LANG6
# 0:0x96, # HID_KEY_LANG7
# 0:0x97, # HID_KEY_LANG8
# 0:0x98, # HID_KEY_LANG9
# 0:0x99, # HID_KEY_ALTERNATE_ERASE
# 0:0x9A, # HID_KEY_SYSREQ_ATTENTION
# 0:0x9B, # HID_KEY_CANCEL
# 0:0x9C, # HID_KEY_CLEAR
# 0:0x9D, # HID_KEY_PRIOR
# 0:0x9E, # HID_KEY_RETURN
# 0:0x9F, # HID_KEY_SEPARATOR
# 0:0xA0, # HID_KEY_OUT
# 0:0xA1, # HID_KEY_OPER
# 0:0xA2, # HID_KEY_CLEAR_AGAIN
# 0:0xA3, # HID_KEY_CRSEL_PROPS
# 0:0xA4, # HID_KEY_EXSEL
# 0:0xE0, # HID_KEY_CONTROL_LEFT
# 0:0xE1, # HID_KEY_SHIFT_LEFT
# 0:0xE2, # HID_KEY_ALT_LEFT
# 0:0xE3, # HID_KEY_GUI_LEFT
# 0:0xE4, # HID_KEY_CONTROL_RIGHT
# 0:0xE5, # HID_KEY_SHIFT_RIGHT
# 0:0xE6, # HID_KEY_ALT_RIGHT
# 0:0xE7, # HID_KEY_GUI_RIGHT
})

def send_keycode(modifier, keycode):
    code = [scan_code_to_hid_key_code[c] for c in keycode] + [0] * 6
    event_data = struct.pack('BB6B', 0xbd, modifier, *code[:6])
    # print('Send', event_data)
    with lock:
        ser.write(event_data)

def on_key_event(event):
    global modifier
    global keycode
    # print(event.to_json(ensure_ascii=sys.stdout.encoding != 'utf-8'))
    # print(event)
    print(
        event.event_type,
        event.scan_code,
        event.name,
        # event.time,
        # event.device,
        # event.modifiers,
        # event.is_keypad
        )
    special_code = [112, 41, 58] # 半角／全角・カタカナ／ローマ字・Caps Lock
    special_case = False
    if event.scan_code in special_code:
        if event.event_type == 'down':
            # upが先に来るパターンとupが来ないケースに対応するため
            modifier |= event_name_to_modifier[event.name]
            keycode.add(event.scan_code)
            special_case = True
    else:
        if event.event_type == 'down':
            modifier |= event_name_to_modifier[event.name]
            keycode.add(event.scan_code)
        elif event.event_type == 'up':
            modifier &= ~event_name_to_modifier[event.name]
            # 複数のキーに同じコードを割り当てていた場合にUPが連続してくる場合がある
            if event.scan_code in keycode:
                keycode.remove(event.scan_code)

    print(modifier, keycode)
    send_keycode(modifier, keycode)

    if special_case:
        modifier ^= event_name_to_modifier[event.name]
        keycode.remove(event.scan_code)
        send_keycode(modifier, keycode)

keyboard.hook(on_key_event)
# keyboard.wait('esc')
# keyboard.wait()

try:
    while True:
        with cond:
            cond.wait(timeout=1)
            if mouse_set_req:
                mouse_x = center_x
                mouse_y = center_y
                mouse_skip_n = 2
                mouse_set_req = False
                mouse_controller.position = (center_x / display_scale, center_y / display_scale)
except:
    pass
