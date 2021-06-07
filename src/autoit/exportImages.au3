#include <MsgBoxConstants.au3>
Local $hWnd = WinWaitActive("Archi - " & $CmdLine[1] & "\src_doc\model\");
Sleep(400);
; set eng keyboard
_SetKeyboardLayout("00000409", $hWnd)
Sleep(400);
Local $imageScale = 100;
Local $project_dir_png = $CmdLine[1] & "\temp\img_exported";
Local $project_dir_svg = $CmdLine[1] & "\temp\img_exported_svg";
Local $project_dir = $project_dir_svg;
Local $stopAfterTheFirst = false;
Local $stop = false;

If ($CmdLine[0] >= 2) Then
	Local $onlyItem = '\' & StringReplace($CmdLine[2], "/", "\")
EndIf;


Sleep(400);

; export ALL
exportItem("#0|#8", "");

; export BA image 
;exportImage("#0|#8|#0|#8", "\01-Business\BA 05 sprava registra");

; export AA image
;exportItem("#0|#8|#1|#3", "\02-Application\AA 00c compoments functions");

; export BA layer
;~ exportLayer("#0|#8|#0", "01-Business");
; export AA layer
;~ exportLayer("#0|#8|#1", "02-Application");

Func _GetKeyboardLayout($hWnd)
    Local $ret = DllCall("user32.dll", "long", "GetWindowThreadProcessId", "hwnd", $hWnd, "ptr", 0)
          $ret = DllCall("user32.dll", "long", "GetKeyboardLayout", "long", $ret[0])
          Return "0000" & Hex($ret[0], 4)
EndFunc

Func _SetKeyboardLayout($sLayoutID, $hWnd)
    Local $WM_INPUTLANGCHANGEREQUEST = 0x50
    Local $ret = DllCall("user32.dll", "long", "LoadKeyboardLayout", "str", $sLayoutID, "int", 0)
    DllCall("user32.dll", "ptr", "SendMessage", "hwnd", $hWnd, _
                                                "int", $WM_INPUTLANGCHANGEREQUEST, _
                                                "int", 1, _
                                                "int", $ret[0])
EndFunc

Func exportItem($itemID, $pathName)
	Local $itemCount = ControlTreeView($hWnd, "", "[CLASS:SysTreeView32; INSTANCE:1]", "GetItemCount", $itemID);
	Local $itemName = ControlTreeView($hWnd, "", "[CLASS:SysTreeView32; INSTANCE:1]", "GetText", $itemID);
	
	; ignore old views
	If ($itemName == 'xOld') Then
		Return;
	EndIf;

	If ($itemCount > 0) Then
		; process layer
		exportLayer($itemID, $pathName);
	Else
		; process image
		exportImage($itemID, $pathName);
	EndIf;
EndFunc

Func exportLayer($layerID, $layerName)
	If ($layerName <> "" ) Then
		DirCreate($project_dir & $layerName);
	EndIf;
	Local $itemCount = ControlTreeView($hWnd, "", "[CLASS:SysTreeView32; INSTANCE:1]", "GetItemCount", $layerID);
	For $i = 0 To ($itemCount-1) Step 1
		Local $itemID = $layerID & "|#" & String($i);
		Local $itemName = ControlTreeView($hWnd, "", "[CLASS:SysTreeView32; INSTANCE:1]", "GetText", $itemID);
		exportItem($itemID, $layerName & '\' & $itemName);
		If ($stop) Then
			Return;
		EndIf;
	Next
EndFunc

Func exportImage($itemID, $itemName)
	If IsDeclared("onlyItem") Then
		If $onlyItem <> $itemName Then
			Return;
		EndIf;
	EndIf;

	;MsgBox($MB_SYSTEMMODAL, "Title", "itemID : " & $itemID, 10)
	;MsgBox($MB_SYSTEMMODAL, "Title", "itemName : " & $sText, 10)
	; select item
	ControlFocus($hWnd, "", "[CLASS:SysTreeView32; INSTANCE:1]");
	ControlTreeView($hWnd, "", "[CLASS:SysTreeView32; INSTANCE:1]", "Select", $itemID);
	Sleep(500);
	; open view
	Send("{ENTER}");
	Sleep(800);
	; open export dialog
	Send("!fe{UP}{ENTER}");
	; fill export data
	;~ Sleep(2000);
    Send("^a{DEL}");
    
    ; PNG
    ;Send($project_dir_png & $itemName & ".png");
	;Send("{TAB}{TAB}{HOME} {DOWN} {DOWN} {DOWN}");
	;Send("{TAB}" & $imageScale);
	;Send("{ENTER}{ENTER}");
    
    ; SVG
	Send($project_dir_svg & $itemName & ".svg");
    Send("{TAB}{TAB}{HOME} {DOWN} {DOWN} {DOWN} {DOWN}");
	If ($stopAfterTheFirst) Then
		$stop = true;
	Else
		Send("^{ENTER}{ENTER}");
	EndIf;
    
    Sleep(500);
EndFunc