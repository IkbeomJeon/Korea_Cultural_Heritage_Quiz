import os
import json
import random
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import yaml

class QuizApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("한국사 퀴즈")
        self.root.geometry("700x1150")
        
        self.image_folder_name= "legacy_images"
        # 데이터 저장 파일
        self.config_file = "quiz_config.json"
        self.stats_file = "quiz_stats.json"
        
        # 설정 및 통계 로드
        self.config = self.load_config()
        self.stats = self.load_stats()
        
        # 창 크기 및 위치 복원
        geometry = self.config.get('window_geometry', '700x1150')
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
        self.quiz_mode = None  # 'artifact' or 'choice'
        
        # 타이머 ID
        self.after_id = None
        
        # output 폴더에서 카테고리 로드
        self.load_categories()
        
        # YAML 파일에서 선지 데이터 로드
        self.choice_data = {}
        self.load_choice_data()
        
        # 초기 화면 표시 (모드 선택)
        self.show_mode_selection_screen()

    def load_config(self):
        """설정 로드"""
        if Path(self.config_file).exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "selected_categories": [],
            "accuracy_filter": 100,
            "show_artifact_name": True,
            "auto_next_delay": 1.5,
            "prioritize_wrong_answers": False,
            "quiz_mode": "artifact"
        }

    def on_closing(self):
        """프로그램 종료 시 창 위치 저장"""
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
    
    def load_choice_data(self):
        """YAML 파일에서 선지 데이터 로드"""
        yaml_file = Path("choices.yaml")
        if not yaml_file.exists():
            print("choices.yaml 파일이 없습니다.")
            return
        
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                self.choice_data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"YAML 파일 로드 실패: {e}")
            self.choice_data = {}
    
    def show_mode_selection_screen(self):
        """1단계: 모드 선택 화면"""
        # 기존 위젯 제거
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 타이틀
        title = tk.Label(self.root, text="학습 모드 선택", 
                        font=("맑은 고딕", 16, "bold"))
        title.pack(pady=30)
        
        # 모드 선택 프레임
        mode_frame = tk.Frame(self.root)
        mode_frame.pack(pady=20)
        
        self.mode_var = tk.StringVar(value=self.config.get('quiz_mode', 'artifact'))
        
        rb_artifact = tk.Radiobutton(mode_frame, text="유물맞추기", 
                                     variable=self.mode_var, value='artifact',
                                     font=("맑은 고딕", 14))
        rb_artifact.pack(anchor='w', pady=10, padx=20)
        
        rb_choice = tk.Radiobutton(mode_frame, text="선지맞추기", 
                                   variable=self.mode_var, value='choice',
                                   font=("맑은 고딕", 14))
        rb_choice.pack(anchor='w', pady=10, padx=20)
        
        # 구분선
        separator = tk.Frame(self.root, height=2, bg='gray')
        separator.pack(fill='x', padx=20, pady=30)
        
        # 공통 옵션 프레임
        options_frame = tk.Frame(self.root)
        options_frame.pack(pady=10)
        
        # 정답률 필터
        filter_frame = tk.Frame(options_frame)
        filter_frame.pack(pady=10)
        
        tk.Label(filter_frame, text="정답률", 
                font=("맑은 고딕", 12)).pack(side='left', padx=5)
        
        self.accuracy_var = tk.IntVar(value=self.config.get('accuracy_filter', 100))
        accuracy_spinbox = tk.Spinbox(filter_frame, from_=0, to=100, 
                                     textvariable=self.accuracy_var,
                                     width=10, font=("맑은 고딕", 12))
        accuracy_spinbox.pack(side='left', padx=5)
        
        tk.Label(filter_frame, text="% 이하만 출제", 
                font=("맑은 고딕", 12)).pack(side='left', padx=5)
        
        # 오답률 우선보기
        self.prioritize_wrong_var = tk.BooleanVar(
            value=self.config.get('prioritize_wrong_answers', False))
        prioritize_cb = tk.Checkbutton(options_frame, 
                                       text="오답률이 높은 항목 우선보기",
                                       variable=self.prioritize_wrong_var,
                                       font=("맑은 고딕", 12))
        prioritize_cb.pack(pady=10)
        
        # 자동 넘기기
        auto_next_frame = tk.Frame(options_frame)
        auto_next_frame.pack(pady=10)
        
        self.auto_next_var = tk.BooleanVar(
            value=self.config.get('auto_next_delay', 1.5) > 0)
        auto_next_cb = tk.Checkbutton(auto_next_frame, 
                                      variable=self.auto_next_var,
                                      font=("맑은 고딕", 12))
        auto_next_cb.pack(side='left')
        
        self.delay_var = tk.DoubleVar(
            value=self.config.get('auto_next_delay', 1.5))
        delay_spinbox = tk.Spinbox(auto_next_frame, 
                                   from_=0, to=10, increment=0.5,
                                   textvariable=self.delay_var,
                                   width=6, font=("맑은 고딕", 12))
        delay_spinbox.pack(side='left', padx=5)
        
        tk.Label(auto_next_frame, text="초 후 다음 문제 자동 넘기기",
                font=("맑은 고딕", 12)).pack(side='left', padx=5)
        
        # 확인 버튼
        confirm_btn = tk.Button(self.root, text="확인", 
                               command=self.proceed_to_detail_screen,
                               font=("맑은 고딕", 14, "bold"),
                               bg="#4CAF50", fg="white",
                               padx=40, pady=10)
        confirm_btn.pack(pady=40)
    
    def proceed_to_detail_screen(self):
        """공통 옵션 저장 후 모드별 상세 설정 화면으로 이동"""
        # 공통 설정 저장
        self.quiz_mode = self.mode_var.get()
        self.config['quiz_mode'] = self.quiz_mode
        self.config['accuracy_filter'] = self.accuracy_var.get()
        self.config['prioritize_wrong_answers'] = self.prioritize_wrong_var.get()
        
        if self.auto_next_var.get():
            self.config['auto_next_delay'] = self.delay_var.get()
        else:
            self.config['auto_next_delay'] = 0
        
        self.save_config()
        
        # 모드에 따라 다른 화면으로 이동
        if self.quiz_mode == 'artifact':
            self.show_artifact_setup_screen()
        elif self.quiz_mode == 'choice':
            self.show_choice_setup_screen()
    
    def show_artifact_setup_screen(self):
        """2단계: 유물맞추기 상세 설정 화면"""
        # 기존 위젯 제거
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 타이틀
        title = tk.Label(self.root, text="유물맞추기 설정", 
                        font=("맑은 고딕", 16, "bold"))
        title.pack(pady=20)
        
        # 시대 선택 안내
        tk.Label(self.root, text="학습할 시대 선택:", 
                font=("맑은 고딕", 12)).pack(pady=10)
        
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
        
        # 구분선
        separator = tk.Frame(self.root, height=2, bg='gray')
        separator.pack(fill='x', padx=20, pady=20)
        
        # 유물맞추기 전용 옵션
        options_frame = tk.Frame(self.root)
        options_frame.pack(pady=10)
        
        # 유물명 같이 보기
        self.show_name_var = tk.BooleanVar(
            value=self.config.get('show_artifact_name', True))
        show_name_cb = tk.Checkbutton(options_frame, 
                                      text="유물명과 같이 보기",
                                      variable=self.show_name_var,
                                      font=("맑은 고딕", 12))
        show_name_cb.pack(pady=10)
        
        # 버튼 프레임
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=30)
        
        # 뒤로가기 버튼
        back_btn = tk.Button(btn_frame, text="← 뒤로", 
                            command=self.show_mode_selection_screen,
                            font=("맑은 고딕", 12),
                            bg="#9E9E9E", fg="white",
                            padx=20, pady=10)
        back_btn.pack(side='left', padx=10)
        
        # 학습 시작 버튼
        start_btn = tk.Button(btn_frame, text="학습 시작", 
                             command=self.start_artifact_quiz,
                             font=("맑은 고딕", 14, "bold"),
                             bg="#4CAF50", fg="white",
                             padx=40, pady=10)
        start_btn.pack(side='left', padx=10)
    
    def show_choice_setup_screen(self):
        """2단계: 선지맞추기 상세 설정 화면"""
        # 기존 위젯 제거
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 타이틀
        title = tk.Label(self.root, text="선지맞추기 설정", 
                        font=("맑은 고딕", 16, "bold"))
        title.pack(pady=20)
        
        # 대분류 선택 안내
        tk.Label(self.root, text="학습할 주제 선택:", 
                font=("맑은 고딕", 12)).pack(pady=10)
        
        # 체크박스 프레임
        checkbox_frame = tk.Frame(self.root)
        checkbox_frame.pack(pady=10)
        
        # 체크박스 변수 저장
        self.choice_checkbox_vars = {}
        
        # YAML 데이터의 대분류(키)로 체크박스 생성
        choice_categories = list(self.choice_data.keys())
        
        for i, category in enumerate(choice_categories):
            var = tk.BooleanVar()
            # 이전 설정 복원
            if category in self.config.get('selected_choice_categories', []):
                var.set(True)
            
            cb = tk.Checkbutton(checkbox_frame, text=category, 
                               variable=var, font=("맑은 고딕", 11),
                               anchor='w')
            cb.pack(anchor='w', padx=20, pady=5)
            self.choice_checkbox_vars[category] = var
        
        # 버튼 프레임
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=30)
        
        # 뒤로가기 버튼
        back_btn = tk.Button(btn_frame, text="← 뒤로", 
                            command=self.show_mode_selection_screen,
                            font=("맑은 고딕", 12),
                            bg="#9E9E9E", fg="white",
                            padx=20, pady=10)
        back_btn.pack(side='left', padx=10)
        
        # 학습 시작 버튼
        start_btn = tk.Button(btn_frame, text="학습 시작", 
                             command=self.start_choice_quiz,
                             font=("맑은 고딕", 14, "bold"),
                             bg="#4CAF50", fg="white",
                             padx=40, pady=10)
        start_btn.pack(side='left', padx=10)
    
    def start_choice_quiz(self):
        """선지맞추기 퀴즈 시작"""
        # 선택된 대분류 가져오기
        selected_choice_categories = [name for name, var in self.choice_checkbox_vars.items() 
                                     if var.get()]
        
        if not selected_choice_categories:
            messagebox.showwarning("경고", "최소 1개 이상 선택해주세요.")
            return
        
        # 설정 저장
        self.config['selected_choice_categories'] = selected_choice_categories
        self.save_config()
        
        # 퀴즈 데이터 준비
        self.prepare_choice_quiz_data(selected_choice_categories)
        
        if not self.quiz_data:
            messagebox.showinfo("알림", "출제할 문제가 없습니다.")
            return
        
        # 퀴즈 화면으로 전환
        self.current_question = 0
        self.correct_count = 0
        self.total_questions = len(self.quiz_data)
        self.show_choice_quiz_screen()
    
    def prepare_choice_quiz_data(self, selected_categories):
        """선지맞추기 퀴즈 데이터 준비"""
        all_questions = []
        accuracy_filter = self.config['accuracy_filter']
        
        for category in selected_categories:
            if category not in self.choice_data:
                continue
            
            items = self.choice_data[category]
            if not isinstance(items, dict):
                continue
            
            # 해당 카테고리의 모든 소분류(항목) 이름 = 보기
            choices = list(items.keys())
            
            # 각 소분류의 모든 선지를 문제로 생성
            for item_name, descriptions in items.items():
                if not isinstance(descriptions, list):
                    continue
                
                for description in descriptions:
                    # 통계 키 생성
                    stats_key = f"{category}|{item_name}|{description}"
                    
                    # 정답률 계산
                    accuracy = 100
                    if stats_key in self.stats:
                        stat = self.stats[stats_key]
                        if stat['total'] > 0:
                            accuracy = (stat['correct'] / stat['total'] * 100)
                    
                    # 정답률 필터링
                    if accuracy > accuracy_filter:
                        continue
                    
                    all_questions.append({
                        'category': category,
                        'question': description,
                        'answer': item_name,
                        'choices': choices,
                        'stats_key': stats_key,
                        'accuracy': accuracy
                    })
        
        # 오답률 우선보기 옵션 적용
        if self.config.get('prioritize_wrong_answers', False):
            # 먼저 랜덤 섞기 (같은 정답률끼리 랜덤하게)
            random.shuffle(all_questions)
            # 그 다음 정답률 낮은 순으로 정렬 (Python의 sort는 stable sort라 같은 값은 기존 순서 유지)
            all_questions.sort(key=lambda x: x['accuracy'])
            print(f"[DEBUG] 오답률 우선보기 활성화 - 정답률 순으로 정렬 (같은 정답률은 랜덤)")
        else:
            # 완전히 랜덤 섞기 (모든 카테고리의 문제가 섞임)
            print(f"[DEBUG] 랜덤 섞기 전 첫 3문제:")
            for i, q in enumerate(all_questions[:3]):
                print(f"  {i+1}. {q['answer']}: {q['question'][:30]}...")
            
            random.shuffle(all_questions)
            
            print(f"[DEBUG] 랜덤 섞기 후 첫 3문제:")
            for i, q in enumerate(all_questions[:3]):
                print(f"  {i+1}. {q['answer']}: {q['question'][:30]}...")
        
        self.quiz_data = all_questions
        print(f"[DEBUG] 총 {len(self.quiz_data)}개 문제 준비 완료")
    
    def show_choice_quiz_screen(self):
        """선지맞추기 퀴즈 화면 표시"""
        # 기존 위젯 제거
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 창 제목 업데이트
        self.root.title(f"{self.current_question + 1}/{self.total_questions}")
        
        current_data = self.quiz_data[self.current_question]
        
        # 카테고리 표시
        category_label = tk.Label(self.root, 
                                 text=f"📁 {current_data['category']}",
                                 font=("맑은 고딕", 11),
                                 fg='gray')
        category_label.pack(pady=(20, 10))
        
        # 정답률 표시
        stats_key = current_data['stats_key']
        if stats_key in self.stats:
            stat = self.stats[stats_key]
            total = stat['total']
            correct_count = stat['correct']
            accuracy = current_data['accuracy']
            
            stats_text = f"📊 누적 정답률: {accuracy:.1f}% ({correct_count}/{total}회)"
            color = 'green' if accuracy >= 70 else 'orange' if accuracy >= 40 else 'red'
            
            stats_label = tk.Label(self.root, text=stats_text,
                                  font=("맑은 고딕", 11),
                                  fg=color)
            stats_label.pack(pady=5)
        else:
            stats_label = tk.Label(self.root, text="📊 첫 도전!",
                                  font=("맑은 고딕", 11),
                                  fg='gray')
            stats_label.pack(pady=5)
        
        # 구분선
        separator = tk.Frame(self.root, height=2, bg='lightgray')
        separator.pack(fill='x', padx=20, pady=20)
        
        # 문제 표시
        question_frame = tk.Frame(self.root, bg='#f0f0f0', relief='solid', bd=1)
        question_frame.pack(pady=20, padx=40, fill='both', expand=True)
        
        question_label = tk.Label(question_frame, 
                                 text=current_data['question'],
                                 font=("맑은 고딕", 14, "bold"),
                                 wraplength=600,
                                 justify='left',
                                 bg='#f0f0f0',
                                 padx=20, pady=20)
        question_label.pack(expand=True)
        
        # 보기 안내
        tk.Label(self.root, text="정답을 선택하세요:",
                font=("맑은 고딕", 12)).pack(pady=(20, 10))
        
        # 보기 버튼
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(pady=10)
        
        choices = current_data['choices']
        
        # 가장 긴 텍스트 길이 계산
        max_length = max(len(choice) for choice in choices) if choices else 10
        button_width = max(12, min(max_length + 2, 30))  # 최소 12, 최대 30
        
        # 한 줄에 3개씩 배치
        for i, choice in enumerate(choices):
            row = i // 3
            col = i % 3
            
            btn = tk.Button(buttons_frame, text=choice,
                          command=lambda c=choice: self.check_choice_answer(c),
                          font=("맑은 고딕", 11),
                          width=button_width, height=2,
                          bg='white', relief='solid', bd=1,
                          wraplength=button_width * 8)  # 글자 길이에 따라 자동 줄바꿈
            btn.grid(row=row, column=col, padx=8, pady=8)
    
    def check_choice_answer(self, user_answer):
        """선지맞추기 정답 체크"""
        if not user_answer:
            return
        
        current_data = self.quiz_data[self.current_question]
        correct_answer = current_data['answer']
        stats_key = current_data['stats_key']
        
        # 정답 여부
        is_correct = (user_answer.strip() == correct_answer)
        
        # 통계 업데이트
        if stats_key not in self.stats:
            self.stats[stats_key] = {'total': 0, 'correct': 0}
        
        self.stats[stats_key]['total'] += 1
        if is_correct:
            self.stats[stats_key]['correct'] += 1
            self.correct_count += 1
        
        # 통계 저장
        self.save_stats()
        
        # 피드백 표시
        self.show_choice_feedback(is_correct, correct_answer, current_data['question'])
    
    def show_choice_feedback(self, is_correct, correct_answer, question):
        """선지맞추기 피드백 표시"""
        # 기존 위젯 제거
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.title(f"{self.current_question + 1}/{self.total_questions}")
        
        # 결과 프레임
        result_frame = tk.Frame(self.root)
        result_frame.pack(expand=True)
        
        # 문제 다시 표시
        tk.Label(result_frame, text=f"문제: {question}",
                font=("맑은 고딕", 12),
                wraplength=600).pack(pady=10)

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
                    fg='blue',
                    font=("맑은 고딕", 16)).pack(pady=10)
        
    
        
        # 통계 정보 표시
        current_data = self.quiz_data[self.current_question]
        stats_key = current_data['stats_key']
        
        if stats_key in self.stats:
            stat = self.stats[stats_key]
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
            self.after_id = self.root.after(delay_ms, self.next_choice_question)
        else:
            # 수동 넘김 (클릭 대기)
            tk.Label(result_frame, text="[클릭하여 계속]",
                    font=("맑은 고딕", 12),
                    fg='gray').pack(pady=20)
            
            # 클릭 또는 키 입력 대기
            self.root.bind('<Button-1>', lambda e: self.next_choice_question())
            self.root.bind('<Key>', lambda e: self.next_choice_question())
    
    def next_choice_question(self):
        """선지맞추기 다음 문제로"""
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
            self.show_choice_quiz_screen()
    
    def start_artifact_quiz(self):
        """유물맞추기 퀴즈 시작"""
        # 선택된 카테고리 가져오기
        self.selected_categories = [name for name, var in self.checkbox_vars.items() 
                                   if var.get()]
        
        if not self.selected_categories:
            messagebox.showwarning("경고", "최소 1개 이상 선택해주세요.")
            return
        
        # 설정 저장
        self.config['selected_categories'] = self.selected_categories
        self.config['show_artifact_name'] = self.show_name_var.get()
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
                    
                    # 정답률 계산
                    accuracy = 100  # 기본값 (통계 없는 경우)
                    if img_path in self.stats:
                        stat = self.stats[img_path]
                        if stat['total'] > 0:
                            accuracy = (stat['correct'] / stat['total'] * 100)
                    
                    # 정답률 필터링
                    if accuracy > accuracy_filter:
                        continue
                    
                    self.quiz_data.append({
                        'image': img_path,
                        'answer': category['name'],
                        'artifact_name': img_file.name,
                        'accuracy': accuracy
                    })
        
        # 오답률 우선보기 옵션 적용
        if self.config.get('prioritize_wrong_answers', False):
            # 정답률 낮은 순으로 정렬 (오답률 높은 순)
            self.quiz_data.sort(key=lambda x: x['accuracy'])
        else:
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
        img_frame.pack_propagate(False)

        try:
            img = Image.open(current_data['image'])
            
            # 프레임 크기에 맞게 비율 유지하며 축소
            max_width = 790
            max_height = 440
            
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            img_label = tk.Label(img_frame, image=photo, bg='white')
            img_label.image = photo
            img_label.place(relx=0.5, rely=0.5, anchor='center')
            
        except Exception as e:
            tk.Label(img_frame, text=f"이미지 로드 실패: {e}",
                    font=("맑은 고딕", 12)).pack()

        # 유물명 및 정답률 표시 프레임
        info_frame = tk.Frame(self.root)
        info_frame.pack(pady=5)
        
        # 유물명 표시 (같이 보기가 체크된 경우)
        if self.config.get('show_artifact_name', True):
            artifact_label = tk.Label(info_frame, 
                                     text=f"유물명: {current_data['artifact_name']}",
                                     font=("맑은 고딕", 12, "bold"),
                                     fg='blue')
            artifact_label.pack()
        
        # 정답률 표시
        img_path = current_data['image']
        if img_path in self.stats:
            stat = self.stats[img_path]
            total = stat['total']
            correct_count = stat['correct']
            accuracy = current_data['accuracy']
            
            stats_text = f"📊 누적 정답률: {accuracy:.1f}% ({correct_count}/{total}회)"
            color = 'green' if accuracy >= 70 else 'orange' if accuracy >= 40 else 'red'
            
            stats_label = tk.Label(info_frame, text=stats_text,
                                  font=("맑은 고딕", 11),
                                  fg=color)
            stats_label.pack()
        else:
            stats_label = tk.Label(info_frame, text="📊 첫 도전!",
                                  font=("맑은 고딕", 11),
                                  fg='gray')
            stats_label.pack()
        
        # 질문
        tk.Label(self.root, text="이 유물의 시대는?",
                font=("맑은 고딕", 14, "bold")).pack(pady=10)
                
        # 보기 버튼
        tk.Label(self.root, text="또는 아래에서 선택:",
                font=("맑은 고딕", 12)).pack(pady=10)
        
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(pady=10)
        
        # 초기 UI 순서대로 정렬
        sorted_categories = [cat['name'] for cat in self.categories 
                            if cat['name'] in self.selected_categories]

        # 한 줄에 4개씩 배치
        for i, category_name in enumerate(sorted_categories):
            row = i // 4
            col = i % 4
            
            btn = tk.Button(buttons_frame, text=category_name,
                        command=lambda c=category_name: self.check_answer(c),
                        font=("맑은 고딕", 11),
                        width=10, height=2,
                        bg='white', relief='solid', bd=1)
            btn.grid(row=row, column=col, padx=8, pady=8)
    
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
        
        # 통계 정보 표시
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
                 command=self.show_mode_selection_screen,
                 font=("맑은 고딕", 12),
                 bg="#4CAF50", fg="white",
                 padx=20, pady=10).pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="종료",
            command=self.on_closing,
            font=("맑은 고딕", 12),
            bg="#f44336", fg="white",
            padx=20, pady=10).pack(side='left', padx=10)
    
    def run(self):
        """프로그램 실행"""
        self.root.mainloop()

def main():
    print("=" * 60)
    print("한국사 퀴즈 프로그램 v3.1")
    print("=" * 60)
    
    app = QuizApp()
    app.run()

if __name__ == "__main__":
    main()