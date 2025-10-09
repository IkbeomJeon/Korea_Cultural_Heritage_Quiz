@echo off
echo 빌드 중...
pyinstaller quiz_app.spec

echo output 폴더 복사 중...
xcopy /E /I /Y output dist\한국사유물퀴즈\output

echo 완료!
pause