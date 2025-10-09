import cv2
import os
from pathlib import Path
import numpy as np
from PIL import Image

class ImageCropper:
    def __init__(self, input_folder='input', output_folder='output'):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.current_image = None
        self.original_image = None
        self.display_image = None
        self.image_name = ""
        self.crop_index = 0
        
        # 뷰포트 관련 변수
        self.zoom_level = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.pan_start = None
        self.is_panning = False
        
        # 크롭 관련 변수
        self.drawing = False
        self.start_point = None
        self.end_point = None
        
        # 화면 크기
        self.screen_width = 1200
        self.screen_height = 800
        
        # 지원하는 이미지 확장자
        self.image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.jfif']
        
    def get_image_files(self):
        """input 폴더에서 이미지 파일 목록 가져오기"""
        image_files = []
        input_path = Path(self.input_folder)
        
        if not input_path.exists():
            print(f"'{self.input_folder}' 폴더가 없습니다. 폴더를 생성합니다.")
            input_path.mkdir(parents=True)
            return image_files
        
        for file in input_path.iterdir():
            if file.suffix.lower() in self.image_extensions:
                image_files.append(file)
        
        return sorted(image_files)
    
    def load_image(self, image_path):
        """이미지 로드 (jfif 파일 지원)"""
        try:
            # PIL로 이미지 열기
            pil_image = Image.open(str(image_path))
            
            # RGB로 변환 (RGBA나 다른 모드 처리)
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # numpy 배열로 변환
            img_array = np.array(pil_image)
            
            # RGB에서 BGR로 변환 (OpenCV 형식)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            return img_bgr
        except Exception as e:
            print(f"이미지 로드 실패: {e}")
            return None
    
    def reset_view(self):
        """뷰 초기화"""
        if self.original_image is not None:
            h, w = self.original_image.shape[:2]
            
            # 화면에 맞게 초기 줌 레벨 설정
            zoom_w = self.screen_width / w
            zoom_h = self.screen_height / h
            self.zoom_level = min(zoom_w, zoom_h, 1.0)  # 최대 100%
            
            self.offset_x = 0
            self.offset_y = 0
    
    def get_display_image(self):
        """현재 뷰포트에 맞는 이미지 생성"""
        if self.current_image is None:
            return None
        
        h, w = self.current_image.shape[:2]
        
        # 줌 적용
        new_w = int(w * self.zoom_level)
        new_h = int(h * self.zoom_level)
        
        if new_w <= 0 or new_h <= 0:
            return self.current_image
        
        zoomed = cv2.resize(self.current_image, (new_w, new_h))
        
        # 오프셋 범위 제한
        max_offset_x = max(0, new_w - self.screen_width)
        max_offset_y = max(0, new_h - self.screen_height)
        self.offset_x = max(0, min(self.offset_x, max_offset_x))
        self.offset_y = max(0, min(self.offset_y, max_offset_y))
        
        # 뷰포트 크롭
        x1 = self.offset_x
        y1 = self.offset_y
        x2 = min(x1 + self.screen_width, new_w)
        y2 = min(y1 + self.screen_height, new_h)
        
        display = zoomed[y1:y2, x1:x2]
        
        # 화면 크기에 맞게 패딩
        if display.shape[0] < self.screen_height or display.shape[1] < self.screen_width:
            canvas = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
            canvas[:display.shape[0], :display.shape[1]] = display
            display = canvas
        
        return display
    
    def screen_to_image_coords(self, x, y):
        """화면 좌표를 원본 이미지 좌표로 변환"""
        img_x = int((x + self.offset_x) / self.zoom_level)
        img_y = int((y + self.offset_y) / self.zoom_level)
        return img_x, img_y
    
    def mouse_callback(self, event, x, y, flags, param):
        """마우스 이벤트 처리"""
        # 우클릭 드래그로 팬
        if event == cv2.EVENT_RBUTTONDOWN:
            self.is_panning = True
            self.pan_start = (x, y)
            
        elif event == cv2.EVENT_RBUTTONUP:
            self.is_panning = False
            self.pan_start = None
            
        elif event == cv2.EVENT_MOUSEMOVE and self.is_panning:
            if self.pan_start:
                dx = self.pan_start[0] - x
                dy = self.pan_start[1] - y
                self.offset_x += dx
                self.offset_y += dy
                self.pan_start = (x, y)
        
        # 좌클릭으로 크롭 영역 선택
        elif event == cv2.EVENT_LBUTTONDOWN and not self.is_panning:
            self.drawing = True
            self.start_point = self.screen_to_image_coords(x, y)
            self.end_point = self.start_point
            
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self.end_point = self.screen_to_image_coords(x, y)
            # 사각형 그리기
            temp = self.original_image.copy()
            cv2.rectangle(temp, self.start_point, self.end_point, (0, 0, 255), 2)
            self.current_image = temp
            
        elif event == cv2.EVENT_LBUTTONUP and self.drawing:
            self.drawing = False
            self.end_point = self.screen_to_image_coords(x, y)
            
            # 최종 사각형
            temp = self.original_image.copy()
            cv2.rectangle(temp, self.start_point, self.end_point, (0, 0, 255), 2)
            self.current_image = temp
            
            # 크롭 및 저장
            self.crop_and_save()
            
            # 원본으로 복원
            self.current_image = self.original_image.copy()
        
        # 마우스 휠로 줌
        elif event == cv2.EVENT_MOUSEWHEEL:
            if flags > 0:  # 휠 업 (줌 인)
                self.zoom_level *= 1.1
            else:  # 휠 다운 (줌 아웃)
                self.zoom_level *= 0.9
            
            self.zoom_level = max(0.1, min(5.0, self.zoom_level))
    
    def crop_and_save(self):
        """선택 영역 크롭 및 저장"""
        if self.start_point and self.end_point:
            # 좌표 정렬
            x1 = min(self.start_point[0], self.end_point[0])
            y1 = min(self.start_point[1], self.end_point[1])
            x2 = max(self.start_point[0], self.end_point[0])
            y2 = max(self.start_point[1], self.end_point[1])
            
            # 영역이 너무 작으면 무시
            if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
                print("⚠ 영역이 너무 작습니다. 다시 선택해주세요.")
                return
            
            # 이미지 경계 체크
            height, width = self.original_image.shape[:2]
            x1 = max(0, min(x1, width))
            y1 = max(0, min(y1, height))
            x2 = max(0, min(x2, width))
            y2 = max(0, min(y2, height))
            
            # 크롭
            cropped = self.original_image[y1:y2, x1:x2].copy()
            
            if cropped.size == 0:
                print("⚠ 크롭된 이미지가 비어있습니다.")
                return
            
            # 저장 경로 생성
            output_dir = Path(self.output_folder).resolve() / self.image_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            image_path = output_dir / f"{self.crop_index}.png"
            
            # 저장 시도
            try:
                # cv2.imwrite로 저장
                encode_param = [int(cv2.IMWRITE_PNG_COMPRESSION), 3]
                success = cv2.imwrite(str(image_path), cropped, encode_param)
                
                if not success or not image_path.exists():
                    # PIL로 재시도
                    rgb_image = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb_image)
                    pil_img.save(str(image_path))
                
                if image_path.exists():
                    file_size = image_path.stat().st_size
                    print(f"✓ 저장완료 [{self.crop_index}]: {image_path.name} ({file_size:,} bytes)")
                    self.crop_index += 1
                else:
                    print(f"❌ 저장 실패")
                    
            except Exception as e:
                print(f"❌ 저장 오류: {e}")
    
    def draw_info(self, img):
        """화면에 정보 표시"""
        info_img = img.copy()
        
        # 반투명 배경
        overlay = info_img.copy()
        cv2.rectangle(overlay, (10, 10), (400, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, info_img, 0.3, 0, info_img)
        
        # 정보 텍스트
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(info_img, f"Zoom: {self.zoom_level:.1f}x", (20, 35), font, 0.6, (255, 255, 255), 1)
        cv2.putText(info_img, f"Crops: {self.crop_index}", (20, 60), font, 0.6, (255, 255, 255), 1)
        cv2.putText(info_img, "Left Click: Crop", (20, 85), font, 0.5, (0, 255, 0), 1)
        cv2.putText(info_img, "Right Drag: Pan | Wheel: Zoom", (20, 105), font, 0.5, (0, 255, 255), 1)
        
        return info_img
    
    def process_image(self, image_path):
        """이미지 처리"""
        self.original_image = self.load_image(image_path)
        
        if self.original_image is None:
            print(f"⚠ 이미지를 불러올 수 없습니다: {image_path}")
            return False
        
        self.current_image = self.original_image.copy()
        self.image_name = image_path.stem
        self.crop_index = 0
        
        # 뷰 초기화
        self.reset_view()
        
        h, w = self.original_image.shape[:2]
        print(f"\n{'='*60}")
        print(f"📷 현재 이미지: {image_path.name}")
        print(f"   크기: {w}x{h} | 초기 줌: {self.zoom_level:.1%}")
        print(f"{'='*60}")
        print("🖱️  좌클릭 드래그: 영역 선택")
        print("🖱️  우클릭 드래그: 이미지 이동")
        print("🖱️  마우스 휠: 확대/축소")
        print("⌨️  R: 뷰 리셋 | Space: 다음 | ESC: 종료")
        
        return True
    
    def run(self):
        """메인 실행"""
        image_path = Path(self.output_folder)
        image_path.mkdir(parents=True, exist_ok=True)
        
        image_files = self.get_image_files()
        
        if not image_files:
            print(f"⚠ '{self.input_folder}' 폴더에 이미지 파일이 없습니다.")
            return
        
        print(f"\n✓ 총 {len(image_files)}개의 이미지를 찾았습니다.")
        
        cv2.namedWindow('Image Cropper', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Image Cropper', self.screen_width, self.screen_height)
        cv2.setMouseCallback('Image Cropper', self.mouse_callback)
        
        current_idx = 0
        
        while current_idx < len(image_files):
            if not self.process_image(image_files[current_idx]):
                current_idx += 1
                continue
            
            while True:
                # 디스플레이 이미지 생성
                display = self.get_display_image()
                if display is not None:
                    display = self.draw_info(display)
                    cv2.imshow('Image Cropper', display)
                
                key = cv2.waitKey(30) & 0xFF
                
                if key == 27:  # ESC
                    print("\n👋 프로그램 종료")
                    cv2.destroyAllWindows()
                    return
                    
                elif key == 32:  # Space
                    print(f"→ 다음 이미지 (크롭: {self.crop_index}개)")
                    current_idx += 1
                    break
                    
                elif key == ord('r') or key == ord('R'):  # R - 리셋
                    self.reset_view()
                    print("🔄 뷰 리셋")
        
        print("\n✅ 모든 이미지 처리 완료!")
        cv2.destroyAllWindows()

def main():
    print("=" * 60)
    print("🎨 이미지 크롭 프로그램 v2.0 (팬/줌 기능)")
    print("=" * 60)
    
    cropper = ImageCropper(input_folder='source_images', output_folder='output')
    cropper.run()

if __name__ == "__main__":
    main()