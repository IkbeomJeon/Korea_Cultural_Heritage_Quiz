import os
import json
import random
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

class QuizApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("한국사 유물 퀴즈")
        self.root.geometry("700x1150")  # 너비 증가, 높이 감소
        
        self.image_folder_name= "legacy_images"
        # 데이터 저장 파일
        self.config_file = "quiz_config.json"
        self.stats_file = "quiz_stats.json"
        
        # 설정 및 통계 로드
        self.config = self.load_config()
        self.stats = self.load_stats()
        
        # 창 크기 및 위치 복원
        geometry = self.config.get('window_geometry', '"700x1150')
        self.root.geometry(geometry)
        
        # 창 닫을 때 위치 저장
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 퀴즈 데이터
        self.categories = []
        self.selected_categories = []
        self.quiz_data = []
        self.current_question = 0
        self.correct_count = 0
        self.total_questions = 0
        
        # 타이머 ID
        self.after_id = None
        
        # output 폴더에서 카테고리 로드
        self.load_categories()
        
        # 초기 화면 표시
        self.show_setup_screen()

    def load_config(self):
        """설정 로드"""
        if Path(self.config_file).exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "selected_categories": [],
            "accuracy_filter": 100,
            "show_artifact_name": True,
            "auto_next_delay": 1.5
        }

    def on_closing(self):
        """프로그램 종료 시 창 위치 저장"""
        # 창 크기와 위치 저장
        self.config['window_geometry'] = self.root.geometry()
        self.save_config()
        self.root.destroy()
    def save_config(self):
        """설정 저장"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def load_stats(self):
        """통계 로드"""
        if Path(self.stats_file).exists():
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_stats(self):
        """통계 저장"""
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
    
    def load_categories(self):
        """output 폴더에서 카테고리 로드"""
        output_path = Path("output")
        if not output_path.exists():
            print("output 폴더가 없습니다.")
            return
        
        # 숫자 기준으로 정렬
        folders = sorted(output_path.iterdir(), 
                        key=lambda x: int(x.name.split('.')[0]) if '.' in x.name and x.name.split('.')[0].isdigit() else 999)
        
        for folder in folders:
            if folder.is_dir():
                folder_name = folder.name
                if '.' in folder_name:
                    category_name = folder_name.split('.', 1)[1]
                else:
                    category_name = folder_name
                
                self.categories.append({
                    'folder': folder_name,
                    'name': category_name
                })
    
    def show_setup_screen(self):
        """초기 설정 화면"""
        # 기존 위젯 제거
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 타이틀
        title = tk.Label(self.root, text="학습할 항목 선택", 
                        font=("맑은 고딕", 16, "bold"))
        title.pack(pady=20)
        
        # 체크박스 프레임 (3열 그리드)
        checkbox_frame = tk.Frame(self.root)
        checkbox_frame.pack(pady=10)
        
        # 체크박스 변수 저장
        self.checkbox_vars = {}
        
        # 3열로 배치
        for i, category in enumerate(self.categories):
            row = i // 3
            col = i % 3
            
            var = tk.BooleanVar()
            # 이전 설정 복원
            if category['name'] in self.config.get('selected_categories', []):
                var.set(True)
            
            cb = tk.Checkbutton(checkbox_frame, text=category['name'], 
                               variable=var, font=("맑은 고딕", 11),
                               width=15, anchor='w')
            cb.grid(row=row, column=col, padx=10, pady=5, sticky='w')
            self.checkbox_vars[category['name']] = var
        
        # 정답률 필터
        filter_frame = tk.Frame(self.root)
        filter_frame.pack(pady=20)
        
        tk.Label(filter_frame, text="정답률", 
                font=("맑은 고딕", 12)).pack(side='left', padx=5)
        
        self.accuracy_var = tk.IntVar(value=self.config.get('accuracy_filter', 100))
        accuracy_spinbox = tk.Spinbox(filter_frame, from_=0, to=100, 
                                     textvariable=self.accuracy_var,
                                     width=10, font=("맑은 고딕", 12))
        accuracy_spinbox.pack(side='left', padx=5)
        
        tk.Label(filter_frame, text="% 이하만 출제", 
                font=("맑은 고딕", 12)).pack(side='left', padx=5)
        
        # 구분선
        separator = tk.Frame(self.root, height=2, bg='gray')
        separator.pack(fill='x', padx=20, pady=20)
        
        # 옵션 프레임
        options_frame = tk.Frame(self.root)
        options_frame.pack(pady=10)
        
        # 유물명 같이 보기 체크박스
        self.show_name_var = tk.BooleanVar(
            value=self.config.get('show_artifact_name', True))
        show_name_cb = tk.Checkbutton(options_frame, 
                                      text="유물명과 같이 보기",
                                      variable=self.show_name_var,
                                      font=("맑은 고딕", 11))
        show_name_cb.pack(pady=5)
        
        # 자동 넘기기 프레임
        auto_next_frame = tk.Frame(options_frame)
        auto_next_frame.pack(pady=5)
        
        self.auto_next_var = tk.BooleanVar(
            value=self.config.get('auto_next_delay', 1.5) > 0)
        auto_next_cb = tk.Checkbutton(auto_next_frame, 
                                      variable=self.auto_next_var,
                                      font=("맑은 고딕", 11))
        auto_next_cb.pack(side='left')
        
        # 초 입력 (실수)
        self.delay_var = tk.DoubleVar(
            value=self.config.get('auto_next_delay', 1.5))
        delay_spinbox = tk.Spinbox(auto_next_frame, 
                                   from_=0, to=10, increment=0.5,
                                   textvariable=self.delay_var,
                                   width=6, font=("맑은 고딕", 11))
        delay_spinbox.pack(side='left', padx=5)
        
        tk.Label(auto_next_frame, text="초 후 다음 문제 자동 넘기기",
                font=("맑은 고딕", 11)).pack(side='left', padx=5)
        
        # 확인 버튼
        confirm_btn = tk.Button(self.root, text="확인", 
                               command=self.start_quiz,
                               font=("맑은 고딕", 14, "bold"),
                               bg="#4CAF50", fg="white",
                               padx=40, pady=10)
        confirm_btn.pack(pady=30)
    
    def start_quiz(self):
        """퀴즈 시작"""
        # 선택된 카테고리 가져오기
        self.selected_categories = [name for name, var in self.checkbox_vars.items() 
                                   if var.get()]
        
        if not self.selected_categories:
            messagebox.showwarning("경고", "최소 1개 이상 선택해주세요.")
            return
        
        # 설정 저장
        self.config['selected_categories'] = self.selected_categories
        self.config['accuracy_filter'] = self.accuracy_var.get()
        self.config['show_artifact_name'] = self.show_name_var.get()
        
        # 자동 넘기기 설정
        if self.auto_next_var.get():
            self.config['auto_next_delay'] = self.delay_var.get()
        else:
            self.config['auto_next_delay'] = 0
        
        self.save_config()
        
        # 퀴즈 데이터 준비
        self.prepare_quiz_data()
        
        if not self.quiz_data:
            messagebox.showinfo("알림", "출제할 문제가 없습니다.")
            return
        
        # 퀴즈 화면으로 전환
        self.current_question = 0
        self.correct_count = 0
        self.total_questions = len(self.quiz_data)
        self.show_quiz_screen()
    
    def prepare_quiz_data(self):
        """퀴즈 데이터 준비"""
        self.quiz_data = []
        accuracy_filter = self.config['accuracy_filter']
        
        output_path = Path(self.image_folder_name)
        
        for category in self.categories:
            if category['name'] not in self.selected_categories:
                continue
            
            folder_path = output_path / category['folder']
            
            # 이미지 파일 찾기 (png, jpg, jpeg)
            for img_file in folder_path.glob("*"):
                if img_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                    img_path = str(img_file)
                    
                    # 정답률 체크
                    if img_path in self.stats:
                        stat = self.stats[img_path]
                        accuracy = (stat['correct'] / stat['total'] * 100) if stat['total'] > 0 else 0
                        
                        if accuracy > accuracy_filter:
                            continue  # 필터링
                    
                    self.quiz_data.append({
                        'image': img_path,
                        'answer': category['name'],
                        'artifact_name': img_file.name  # 파일명 저장
                    })
        
        # 셔플
        random.shuffle(self.quiz_data)
    
    def show_quiz_screen(self):
        """퀴즈 화면 표시"""
        # 기존 위젯 제거
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 창 제목 업데이트
        self.root.title(f"{self.current_question + 1}/{self.total_questions}")
        
        current_data = self.quiz_data[self.current_question]
        
        # 이미지 표시
        img_frame = tk.Frame(self.root, bg='white', width=800, height=450)
        img_frame.pack(pady=10, padx=20)
        img_frame.pack_propagate(False)  # 크기 고정

        try:
            img = Image.open(current_data['image'])
            
            # 프레임 크기에 맞게 비율 유지하며 축소 (여백 포함)
            max_width = 790   # 800 - 10
            max_height = 440  # 450 - 10
            
            # 비율 유지하며 리사이즈
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            img_label = tk.Label(img_frame, image=photo, bg='white')
            img_label.image = photo  # 참조 유지
            img_label.place(relx=0.5, rely=0.5, anchor='center')  # 중앙 정렬
            
        except Exception as e:
            tk.Label(img_frame, text=f"이미지 로드 실패: {e}",
                    font=("맑은 고딕", 12)).pack()

        
        # 유물명 표시 (같이 보기가 체크된 경우)
        if self.config.get('show_artifact_name', True):
            artifact_label = tk.Label(self.root, 
                                     text=f"유물명: {current_data['artifact_name']}",
                                     font=("맑은 고딕", 12, "bold"),
                                     fg='blue')
            artifact_label.pack(pady=5)
        
        # 질문
        tk.Label(self.root, text="이 유물의 시대는?",
                font=("맑은 고딕", 14, "bold")).pack(pady=10)
                
        # 보기 버튼
        tk.Label(self.root, text="또는 아래에서 선택:",
                font=("맑은 고딕", 12)).pack(pady=10)
        
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(pady=10)
        
        # 초기 UI 순서대로 정렬
        # 초기 UI 순서(self.categories)대로 정렬
        sorted_categories = [cat['name'] for cat in self.categories 
                            if cat['name'] in self.selected_categories]

        # 한 줄에 4개씩 배치
        for i, category_name in enumerate(sorted_categories):
            row = i // 4
            col = i % 4
            
            btn = tk.Button(buttons_frame, text=category_name,
                        command=lambda c=category_name: self.check_answer(c),
                        font=("맑은 고딕", 10),
                        width=9, height=2,
                        bg='white', relief='solid', bd=1)
            btn.grid(row=row, column=col, padx=6, pady=8)
            
            btn = tk.Button(buttons_frame, text=category_name,
                        command=lambda c=category_name: self.check_answer(c),
                        font=("맑은 고딕", 11),  # 12 → 11로 축소 (선택사항)
                        width=10, height=2,      # 12 → 10으로 축소 (선택사항)
                        bg='white', relief='solid', bd=1)
            btn.grid(row=row, column=col, padx=8, pady=8)  # 여백 약간 조정 (선택사항)
    
    def check_answer(self, user_answer):
        """정답 체크"""
        if not user_answer:
            return
        
        current_data = self.quiz_data[self.current_question]
        correct_answer = current_data['answer']
        artifact_name = current_data['artifact_name']
        img_path = current_data['image']
        
        # 정답 여부
        is_correct = (user_answer.strip() == correct_answer)
        
        # 통계 업데이트
        if img_path not in self.stats:
            self.stats[img_path] = {'total': 0, 'correct': 0}
        
        self.stats[img_path]['total'] += 1
        if is_correct:
            self.stats[img_path]['correct'] += 1
            self.correct_count += 1
        
        # 통계 저장
        self.save_stats()
        
        # 피드백 표시
        self.show_feedback(is_correct, correct_answer, artifact_name)
    
    def show_feedback(self, is_correct, correct_answer, artifact_name):
        """피드백 표시"""
        # 기존 위젯 제거
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.title(f"{self.current_question + 1}/{self.total_questions}")
        
        # 결과 프레임
        result_frame = tk.Frame(self.root)
        result_frame.pack(expand=True)
        
        if is_correct:
            # 정답
            tk.Label(result_frame, text="✓ 정답!",
                    font=("맑은 고딕", 24, "bold"),
                    fg='green').pack(pady=20)
        else:
            # 오답
            tk.Label(result_frame, text="✗ 오답",
                    font=("맑은 고딕", 24, "bold"),
                    fg='red').pack(pady=20)
            tk.Label(result_frame, text=f"정답: {correct_answer}",
                    font=("맑은 고딕", 16)).pack(pady=10)
        
        # 유물명 표시 (항상 표시)
        tk.Label(result_frame, text=f"유물명: {artifact_name}",
                font=("맑은 고딕", 14, "bold"),
                fg='blue').pack(pady=10)
        
        # 통계 정보 표시 추가
        current_data = self.quiz_data[self.current_question]
        img_path = current_data['image']
        
        if img_path in self.stats:
            stat = self.stats[img_path]
            total = stat['total']
            correct_count = stat['correct']
            accuracy = (correct_count / total * 100) if total > 0 else 0
            
            stats_text = f"이 문제 통계: {correct_count}/{total}회 정답 (정답률 {accuracy:.1f}%)"
            tk.Label(result_frame, text=stats_text,
                    font=("맑은 고딕", 12),
                    fg='gray').pack(pady=10)
        
        # 자동 넘기기 설정 확인
        auto_delay = self.config.get('auto_next_delay', 1.5)
        
        if auto_delay > 0:
            # 자동 넘김
            delay_ms = int(auto_delay * 1000)
            self.after_id = self.root.after(delay_ms, self.next_question)
        else:
            # 수동 넘김 (클릭 대기)
            tk.Label(result_frame, text="[클릭하여 계속]",
                    font=("맑은 고딕", 12),
                    fg='gray').pack(pady=20)
            
            # 클릭 또는 키 입력 대기
            self.root.bind('<Button-1>', lambda e: self.next_question())
            self.root.bind('<Key>', lambda e: self.next_question())
    def next_question(self):
        """다음 문제로"""
        # 타이머 취소
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        
        # 이벤트 바인딩 해제
        self.root.unbind('<Button-1>')
        self.root.unbind('<Key>')
        
        self.current_question += 1
        
        if self.current_question >= self.total_questions:
            # 퀴즈 종료
            self.show_result()
        else:
            # 다음 문제 표시
            self.show_quiz_screen()
    
    def show_result(self):
        """결과 화면"""
        # 기존 위젯 제거
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.title("학습 결과")
        
        # 결과 표시
        tk.Label(self.root, text="학습 결과",
                font=("맑은 고딕", 20, "bold")).pack(pady=30)
        
        accuracy = (self.correct_count / self.total_questions * 100) if self.total_questions > 0 else 0
        
        result_frame = tk.Frame(self.root)
        result_frame.pack(pady=20)
        
        results = [
            f"전체: {self.total_questions}문제",
            f"정답: {self.correct_count}문제",
            f"오답: {self.total_questions - self.correct_count}문제",
            f"정답률: {accuracy:.1f}%"
        ]
        
        for result in results:
            tk.Label(result_frame, text=result,
                    font=("맑은 고딕", 14)).pack(pady=5)
        
        # 다시 하기 버튼
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=30)
        
        tk.Button(btn_frame, text="다시 학습하기",
                 command=self.show_setup_screen,
                 font=("맑은 고딕", 12),
                 bg="#4CAF50", fg="white",
                 padx=20, pady=10).pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="종료",
            command=self.on_closing,  # self.root.quit → self.on_closing
            font=("맑은 고딕", 12),
            bg="#f44336", fg="white",
            padx=20, pady=10).pack(side='left', padx=10)
    
    def run(self):
        """프로그램 실행"""
        self.root.mainloop()

def main():
    print("=" * 60)
    print("한국사 유물 퀴즈 프로그램 v2.1")
    print("=" * 60)
    
    app = QuizApp()
    app.run()

if __name__ == "__main__":
    main()