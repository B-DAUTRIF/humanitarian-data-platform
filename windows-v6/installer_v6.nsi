Unicode True
!include "MUI2.nsh"
!include "Sections.nsh"
!include "LogicLib.nsh"

Name "Humanitarian Data Platform V6 API UI"
OutFile "HDP_V6_API_UI_Setup_Windows_x64.exe"
InstallDir "$LOCALAPPDATA\HumanitarianDataPlatform\V6_API_UI"
RequestExecutionLevel user
SetCompressor /SOLID lzma

Var PythonPresent
Var WingetPresent

!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "French"

Section "HDP V6 API UI (requis)" SEC_CORE
  SectionIn RO
  SetOutPath "$INSTDIR"
  File "dist\HDP_V6_API_UI.exe"
  File "README_COMPLET.txt"
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  CreateDirectory "$SMPROGRAMS\Humanitarian Data Platform"
  CreateShortcut "$SMPROGRAMS\Humanitarian Data Platform\HDP V6 API UI.lnk" "$INSTDIR\HDP_V6_API_UI.exe"
  CreateShortcut "$DESKTOP\HDP V6 API UI.lnk" "$INSTDIR\HDP_V6_API_UI.exe"

  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\HDPV6APIUI" "DisplayName" "Humanitarian Data Platform V6 API UI"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\HDPV6APIUI" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\HDPV6APIUI" "DisplayVersion" "6.0.0"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\HDPV6APIUI" "Publisher" "Humanitarian Data Platform"
SectionEnd

Section /o "Python 3.12 pour scripts et traitements HDP" SEC_PYTHON
  ${If} $PythonPresent == "1"
    DetailPrint "Python déjà présent : aucune modification."
    Goto python_done
  ${EndIf}

  ${If} $WingetPresent != "1"
    MessageBox MB_ICONEXCLAMATION|MB_OK "Python n'est pas détecté et winget est indisponible. HDP V6 reste installable, mais les scripts Python externes nécessiteront une installation manuelle de Python 3.12."
    Goto python_done
  ${EndIf}

  DetailPrint "Installation optionnelle de Python 3.12 via Microsoft winget..."
  nsExec::ExecToLog 'winget.exe install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements --silent --disable-interactivity'
  Pop $0
  ${If} $0 != 0
    MessageBox MB_ICONEXCLAMATION|MB_OK "L'installation automatique de Python a échoué (code $0). HDP V6 a néanmoins été installé. Vous pourrez installer Python 3.12 ultérieurement."
  ${Else}
    DetailPrint "Python 3.12 installé avec succès."
  ${EndIf}
python_done:
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\HDP V6 API UI.lnk"
  Delete "$SMPROGRAMS\Humanitarian Data Platform\HDP V6 API UI.lnk"
  RMDir "$SMPROGRAMS\Humanitarian Data Platform"
  Delete "$INSTDIR\HDP_V6_API_UI.exe"
  Delete "$INSTDIR\README_COMPLET.txt"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\HDPV6APIUI"
SectionEnd

Function .onInit
  StrCpy $PythonPresent "0"
  StrCpy $WingetPresent "0"

  nsExec::ExecToStack 'cmd.exe /C "where py.exe >NUL 2>&1 || where python.exe >NUL 2>&1"'
  Pop $0
  Pop $1
  ${If} $0 == 0
    StrCpy $PythonPresent "1"
    !insertmacro UnselectSection ${SEC_PYTHON}
  ${Else}
    !insertmacro SelectSection ${SEC_PYTHON}
  ${EndIf}

  nsExec::ExecToStack 'cmd.exe /C "where winget.exe >NUL 2>&1"'
  Pop $0
  Pop $1
  ${If} $0 == 0
    StrCpy $WingetPresent "1"
  ${EndIf}
FunctionEnd

LangString DESC_CORE ${LANG_FRENCH} "Installe l'interface HDP V6 et son runtime autonome. Python n'est pas nécessaire pour lancer cette interface."
LangString DESC_PYTHON ${LANG_FRENCH} "Propose Python 3.12 pour exécuter et développer des scripts Python dans l'écosystème HDP. Une installation Python existante est conservée."
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_CORE} $(DESC_CORE)
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_PYTHON} $(DESC_PYTHON)
!insertmacro MUI_FUNCTION_DESCRIPTION_END
