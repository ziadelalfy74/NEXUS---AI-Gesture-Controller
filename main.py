import cv2
import numpy as np
import time
import math
import pyautogui
import mediapipe as mp

# إلغاء خاصية الأمان لـ PyAutoGUI
pyautogui.FAILSAFE = False


class GestureMouseEngine:

  def __init__(self, model_path='gesture_recognizer.task'):
    self.model_path = model_path

    # أبعاد الشاشة ومتغيرات التنعيم
    self.screen_width, self.screen_height = pyautogui.size()
    self.prev_x, self.prev_y = 0, 0
    self.smooth_factor = 5
    self.frame_margin = 100

    # إعدادات التوقيت
    self.click_threshold = 35
    self.click_cooldown = 0.3
    self.last_click_time = 0

    self.scroll_cooldown = 0.08
    self.last_scroll_time = 0

    # روابط المفاصل لرسم الهيكل العظمي للجوانتي (Hand Connections)
    self.HAND_CONNECTIONS = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),  # الإبهام
        (0, 5),
        (5, 6),
        (6, 7),
        (7, 8),  # السبابة
        (5, 9),
        (9, 10),
        (10, 11),
        (11, 12),  # الوسطى
        (9, 13),
        (13, 14),
        (14, 15),
        (15, 16),  # البنسر
        (13, 17),
        (17, 18),
        (18, 19),
        (19, 20),  # الخنصر
        (0, 17),  # قاعدة الكف
    ]

  def draw_cyber_glove(self, frame, hand_landmarks, h, w):
    # تحويل كل النقاط لإحداثيات بكسل
    points = []
    for lm in hand_landmarks:
      cx, cy = int(lm.x * w), int(lm.y * h)
      points.append((cx, cy))

    # 1. رسم خطوط الهيكل العظمي المتوهجة (Cyan Glow Lines)
    for start_idx, end_idx in self.HAND_CONNECTIONS:
      p1, p2 = points[start_idx], points[end_idx]
      # طبقة التوهج الخارجية
      cv2.line(frame, p1, p2, (255, 200, 0), 3, cv2.LINE_AA)
      # السلك الداخلي المضيء
      cv2.line(frame, p1, p2, (255, 255, 255), 1, cv2.LINE_AA)

    # 2. رسم العقد والجوينتات (Cyber Joint Nodes)
    for i, p in enumerate(points):
      # أطراف الأصابع تاخد شكل أهداف HUD خاصة
      if i in [4, 8, 12, 16, 20]:
        cv2.circle(frame, p, 9, (255, 229, 0), 2, cv2.LINE_AA)
        cv2.circle(frame, p, 4, (0, 255, 255), cv2.FILLED)
      else:
        cv2.circle(frame, p, 4, (255, 150, 0), cv2.FILLED)
        cv2.circle(frame, p, 2, (255, 255, 255), cv2.FILLED)

    return points

  def process_frame(self, frame, recognizer):
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
    )
    timestamp_ms = int(time.time() * 1000)

    result = recognizer.recognize_for_video(mp_image, timestamp_ms)
    current_gesture = 'NAVIGATING'

    if result.hand_landmarks:
      hand_landmarks = result.hand_landmarks[0]

      # رسم تأثير الجوانتي السايبر وحفظ نقاط الأصابع
      points = self.draw_cyber_glove(frame, hand_landmarks, h, w)

      # --- النقاط والمفاصل الحسابية ---
      index_tip, index_mcp = hand_landmarks[8], hand_landmarks[5]
      middle_tip, middle_mcp = hand_landmarks[12], hand_landmarks[9]
      ring_tip, ring_mcp = hand_landmarks[16], hand_landmarks[13]
      pinky_tip, pinky_mcp = hand_landmarks[20], hand_landmarks[17]

      x1, y1 = points[8]
      x2, y2 = points[12]

      # منطق الحركات المعتمد
      four_pointing_up = (
          index_tip.y < index_mcp.y - 0.04
          and middle_tip.y < middle_mcp.y - 0.04
          and ring_tip.y < ring_mcp.y - 0.04
          and pinky_tip.y < pinky_mcp.y - 0.04
      )

      four_pointing_down = (
          index_tip.y > index_mcp.y + 0.04
          and middle_tip.y > middle_mcp.y + 0.04
          and ring_tip.y > ring_mcp.y + 0.04
          and pinky_tip.y > pinky_mcp.y + 0.04
      )

      is_fist = (
          abs(index_tip.y - index_mcp.y) < 0.04
          and abs(middle_tip.y - middle_mcp.y) < 0.04
          and abs(ring_tip.y - ring_mcp.y) < 0.04
          and abs(pinky_tip.y - pinky_mcp.y) < 0.04
      )

      # --- تنفيذ الأوامر ---
      if is_fist:
        current_gesture = 'PAUSED'
        cv2.putText(
            frame,
            'SYSTEM PAUSED',
            (20, 45),
            cv2.FONT_HERSHEY_DUPLEX,
            0.9,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )

      elif four_pointing_up:
        current_gesture = 'SCROLL UP'
        cv2.putText(
            frame,
            'ACTION: SCROLL UP',
            (20, 45),
            cv2.FONT_HERSHEY_DUPLEX,
            0.9,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        if time.time() - self.last_scroll_time > self.scroll_cooldown:
          pyautogui.scroll(250)
          self.last_scroll_time = time.time()

      elif four_pointing_down:
        current_gesture = 'SCROLL DOWN'
        cv2.putText(
            frame,
            'ACTION: SCROLL DOWN',
            (20, 45),
            cv2.FONT_HERSHEY_DUPLEX,
            0.9,
            (0, 165, 255),
            2,
            cv2.LINE_AA,
        )
        if time.time() - self.last_scroll_time > self.scroll_cooldown:
          pyautogui.scroll(-250)
          self.last_scroll_time = time.time()

      else:
        screen_x = np.interp(
            x1, (self.frame_margin, w - self.frame_margin), (0, self.screen_width)
        )
        screen_y = np.interp(
            y1,
            (self.frame_margin, h - self.frame_margin),
            (0, self.screen_height),
        )

        curr_x = self.prev_x + (screen_x - self.prev_x) / self.smooth_factor
        curr_y = self.prev_y + (screen_y - self.prev_y) / self.smooth_factor

        pyautogui.moveTo(curr_x, curr_y)
        self.prev_x, self.prev_y = curr_x, curr_y

        distance = math.hypot(x2 - x1, y2 - y1)

        if distance < self.click_threshold:
          current_gesture = 'CLICK'
          # تأثير كليك سايبر على السبابة والوسطى
          cv2.circle(frame, (x1, y1), 14, (0, 0, 255), cv2.FILLED)
          cv2.circle(frame, (x1, y1), 20, (0, 0, 255), 2, cv2.LINE_AA)
          if time.time() - self.last_click_time > self.click_cooldown:
            pyautogui.click()
            self.last_click_time = time.time()

    return frame, current_gesture


if __name__ == '__main__':
  engine = GestureMouseEngine()
  BaseOptions = mp.tasks.BaseOptions
  GestureRecognizer = mp.tasks.vision.GestureRecognizer
  GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
  VisionRunningMode = mp.tasks.vision.RunningMode

  options = GestureRecognizerOptions(
      base_options=BaseOptions(model_asset_path=engine.model_path),
      running_mode=VisionRunningMode.VIDEO,
  )

  cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
  cap.set(3, 640)
  cap.set(4, 480)

  with GestureRecognizer.create_from_options(options) as recognizer:
    while cap.isOpened():
      success, frame = cap.read()
      if not success:
        break
      processed_frame, _ = engine.process_frame(frame, recognizer)
      cv2.imshow('Gesture Virtual Mouse Engine', processed_frame)
      if cv2.waitKey(1) & 0xFF == ord('q'):
        break

  cap.release()
  cv2.destroyAllWindows()