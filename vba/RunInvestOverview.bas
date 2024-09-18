Sub RunInvestOverview()
    Dim currentWorkbook As Workbook
    Dim investOverviewPath As String
    Dim currentWorkbookPath As String
    Dim investOverviewExe As String
    Dim shellCommand As String
    Dim folderPath As String
    Dim fileName As String
    Dim fileExists As Boolean
    Dim fileModified As Date
    Dim maxWaitTime As Long
    Dim startTime As Date

    ' Get the path of the current workbook
    Set currentWorkbook = ThisWorkbook
    currentWorkbookPath = currentWorkbook.FullName
    folderPath = currentWorkbook.Path
    fileName = currentWorkbook.Name

    ' Save the current workbook
    currentWorkbook.Save

    ' Define the path of the _investment_overview_python.xlsx file
    investOverviewPath = folderPath & "/_investment_overview_python.xlsx"

    ' Check if the _investment_overview_python.xlsx file exists and get its last modified time
    fileExists = Dir(investOverviewPath) <> ""
    If fileExists Then
        On Error Resume Next
        Workbooks("_investment_overview_python.xlsx").Close SaveChanges:=False
        On Error GoTo 0
        fileModified = FileDateTime(investOverviewPath)
    End If

    ' Define the path of the InvestOverview executable file
    investOverviewExe = folderPath & "/InvestOverview"

    ' Create the shell command to execute the executable file
    shellCommand = """" & investOverviewExe & """ --excel_path """ & currentWorkbookPath & """"

    ' Execute the executable file
    Call Shell(shellCommand, vbNormalFocus)

    ' Wait for the executable to finish executing by checking the file modification time
    maxWaitTime = 300 ' Maximum wait time in seconds
    startTime = Now
    Do
        Application.Wait (Now + TimeValue("0:00:01")) ' Wait for 1 second
        If Dir(investOverviewPath) <> "" Then
            If FileDateTime(investOverviewPath) <> fileModified Then
                Exit Do ' File has been modified, indicating the executable has finished
            End If
        End If
        If DateDiff("s", startTime, Now) > maxWaitTime Then
            Exit Do ' Exit if the maximum wait time is exceeded
        End If
    Loop

    ' Open the _investment_overview_python.xlsx file
    If Dir(investOverviewPath) <> "" Then
        Workbooks.Open investOverviewPath
    End If

    ' Bring the current workbook back to the foreground
    Application.Wait (Now + TimeValue("0:00:01")) ' Wait for 1 second
    currentWorkbook.Activate
End Sub
