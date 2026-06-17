!define TASK_NAME "ComplianceApp"
; ★ 실행 시각 변경: 아래 TASK_TIME 값만 수정하세요 (24시간 형식 HH:MM)
!define TASK_TIME "09:00"

!macro customInstall
  FileOpen $0 "$INSTDIR\task.xml" w
  FileWrite $0 '<?xml version="1.0" encoding="UTF-16"?>'
  FileWrite $0 '<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">'
  FileWrite $0   '<Triggers>'
  FileWrite $0     '<CalendarTrigger>'
  FileWrite $0       '<StartBoundary>2000-01-01T${TASK_TIME}:00</StartBoundary>'
  FileWrite $0       '<Enabled>true</Enabled>'
  FileWrite $0       '<ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>'
  FileWrite $0     '</CalendarTrigger>'
  FileWrite $0     '<LogonTrigger>'
  FileWrite $0       '<Enabled>true</Enabled>'
  FileWrite $0     '</LogonTrigger>'
  FileWrite $0   '</Triggers>'
  FileWrite $0   '<Principals>'
  FileWrite $0     '<Principal id="Author">'
  FileWrite $0       '<LogonType>InteractiveToken</LogonType>'
  FileWrite $0       '<RunLevel>LeastPrivilege</RunLevel>'
  FileWrite $0     '</Principal>'
  FileWrite $0   '</Principals>'
  FileWrite $0   '<Settings>'
  FileWrite $0     '<MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>'
  FileWrite $0     '<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>'
  FileWrite $0     '<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>'
  FileWrite $0     '<ExecutionTimeLimit>PT0S</ExecutionTimeLimit>'
  FileWrite $0     '<RunOnlyIfIdle>false</RunOnlyIfIdle>'
  FileWrite $0     '<StartWhenAvailable>true</StartWhenAvailable>'
  FileWrite $0   '</Settings>'
  FileWrite $0   '<Actions>'
  FileWrite $0     '<Exec>'
  FileWrite $0       '<Command>"$INSTDIR\KBComplianceApp.exe"</Command>'
  FileWrite $0     '</Exec>'
  FileWrite $0   '</Actions>'
  FileWrite $0 '</Task>'
  FileClose $0

  ExecWait 'cmd /c schtasks /delete /tn "${TASK_NAME}" /f'
  ExecWait 'cmd /c schtasks /create /tn "${TASK_NAME}" /xml "$INSTDIR\task.xml" /f' $1
  ${If} $1 != 0
    MessageBox MB_ICONEXCLAMATION|MB_OK "작업 스케줄러 등록 실패 (오류코드: $1)$\n$\n관리자 권한 명령 프롬프트에서 아래 명령을 실행해주세요:$\nschtasks /create /tn ComplianceApp /xml $\"$INSTDIR\task.xml$\" /f"
  ${EndIf}
!macroend

!macro customUnInstall
  ExecWait 'cmd /c schtasks /delete /tn "${TASK_NAME}" /f'
  Delete "$INSTDIR\task.xml"
!macroend
