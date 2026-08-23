using System;
using System.Diagnostics;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace ArcRiseFantasiaKoreanRomPatcher
{
    internal sealed class MainForm : Form
    {
        private readonly TextBox inputBox;
        private readonly TextBox outputBox;
        private readonly ComboBox formatBox;
        private readonly Button inputBrowseButton;
        private readonly Button outputBrowseButton;
        private readonly Button startButton;
        private readonly Button cancelButton;
        private readonly Button openButton;
        private readonly ProgressBar progressBar;
        private readonly Label statusLabel;
        private readonly RichTextBox logBox;
        private CancellationTokenSource cancellation;
        private string completedOutput;

        public MainForm()
        {
            Text = "아크 라이즈 판타지아 한국어 롬 패처 v1.1.1";
            StartPosition = FormStartPosition.CenterScreen;
            MinimumSize = new Size(820, 610);
            Size = new Size(860, 650);
            Font = new Font("Malgun Gothic", 9.5f);
            Icon = SystemIcons.Application;

            Label title = new Label {
                Text = "아크 라이즈 판타지아 한국어판 만들기",
                Dock = DockStyle.Top, Height = 46,
                TextAlign = ContentAlignment.MiddleLeft,
                Font = new Font("Malgun Gothic", 17f, FontStyle.Bold),
                Padding = new Padding(12, 0, 0, 0)
            };
            Label description = new Label {
                Text = "일본판 RPJJ99 원본 RVZ/ISO를 고르면 원본은 그대로 두고 한국어판 복사본을 만듭니다.",
                Dock = DockStyle.Top, Height = 34, Padding = new Padding(15, 3, 0, 0)
            };
            TableLayoutPanel fields = new TableLayoutPanel {
                Dock = DockStyle.Top, Height = 130, Padding = new Padding(12, 6, 12, 4),
                ColumnCount = 3, RowCount = 3
            };
            fields.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 135));
            fields.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            fields.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 92));
            fields.RowStyles.Add(new RowStyle(SizeType.Absolute, 40));
            fields.RowStyles.Add(new RowStyle(SizeType.Absolute, 40));
            fields.RowStyles.Add(new RowStyle(SizeType.Absolute, 40));

            inputBox = new TextBox { Dock = DockStyle.Fill, Margin = new Padding(4, 7, 4, 5) };
            outputBox = new TextBox { Dock = DockStyle.Fill, Margin = new Padding(4, 7, 4, 5) };
            formatBox = new ComboBox {
                Dock = DockStyle.Left, Width = 150,
                DropDownStyle = ComboBoxStyle.DropDownList,
                Margin = new Padding(4, 6, 4, 4)
            };
            formatBox.Items.AddRange(new object[] { "RVZ", "ISO" });
            formatBox.SelectedIndex = 0;
            inputBrowseButton = new Button {
                Text = "찾아보기", Dock = DockStyle.Fill, Margin = new Padding(4)
            };
            outputBrowseButton = new Button {
                Text = "저장 위치", Dock = DockStyle.Fill, Margin = new Padding(4)
            };
            fields.Controls.Add(MakeFieldLabel("일본판 원본"), 0, 0);
            fields.Controls.Add(inputBox, 1, 0);
            fields.Controls.Add(inputBrowseButton, 2, 0);
            fields.Controls.Add(MakeFieldLabel("한국어판 저장"), 0, 1);
            fields.Controls.Add(outputBox, 1, 1);
            fields.Controls.Add(outputBrowseButton, 2, 1);
            fields.Controls.Add(MakeFieldLabel("출력 형식"), 0, 2);
            fields.Controls.Add(formatBox, 1, 2);

            Panel progressPanel = new Panel {
                Dock = DockStyle.Top, Height = 80, Padding = new Padding(15, 7, 15, 5)
            };
            statusLabel = new Label {
                Text = "원본 파일을 선택하세요.", Dock = DockStyle.Top,
                Height = 28, AutoEllipsis = true
            };
            progressBar = new ProgressBar {
                Dock = DockStyle.Top, Height = 24, Minimum = 0, Maximum = 100
            };
            progressPanel.Controls.Add(progressBar);
            progressPanel.Controls.Add(statusLabel);

            FlowLayoutPanel buttons = new FlowLayoutPanel {
                Dock = DockStyle.Bottom, Height = 58,
                FlowDirection = FlowDirection.RightToLeft,
                Padding = new Padding(10, 9, 10, 7)
            };
            startButton = new Button {
                Text = "한국어판 만들기", Width = 155, Height = 35,
                Font = new Font("Malgun Gothic", 10f, FontStyle.Bold)
            };
            cancelButton = new Button { Text = "취소", Width = 90, Height = 35, Enabled = false };
            openButton = new Button {
                Text = "완성 파일 열기", Width = 135, Height = 35, Enabled = false
            };
            buttons.Controls.Add(startButton);
            buttons.Controls.Add(cancelButton);
            buttons.Controls.Add(openButton);

            logBox = new RichTextBox {
                Dock = DockStyle.Fill, ReadOnly = true,
                BackColor = Color.FromArgb(28, 31, 36), ForeColor = Color.Gainsboro,
                Font = new Font("Consolas", 9f), BorderStyle = BorderStyle.FixedSingle
            };
            Panel logPanel = new Panel {
                Dock = DockStyle.Fill, Padding = new Padding(15, 4, 15, 8)
            };
            logPanel.Controls.Add(logBox);

            Controls.Add(logPanel);
            Controls.Add(buttons);
            Controls.Add(progressPanel);
            Controls.Add(fields);
            Controls.Add(description);
            Controls.Add(title);

            inputBrowseButton.Click += InputBrowseButton_Click;
            outputBrowseButton.Click += OutputBrowseButton_Click;
            formatBox.SelectedIndexChanged += FormatBox_SelectedIndexChanged;
            startButton.Click += StartButton_Click;
            cancelButton.Click += CancelButton_Click;
            openButton.Click += OpenButton_Click;
            FormClosing += MainForm_FormClosing;
        }

        private static Label MakeFieldLabel(string text)
        {
            return new Label {
                Text = text, Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleLeft,
                Padding = new Padding(3, 0, 0, 0)
            };
        }

        private void InputBrowseButton_Click(object sender, EventArgs e)
        {
            using (OpenFileDialog dialog = new OpenFileDialog())
            {
                dialog.Title = "일본판 RPJJ99 원본 RVZ/ISO 선택";
                dialog.Filter = "Wii 게임 이미지 (*.rvz;*.iso)|*.rvz;*.iso|모든 파일 (*.*)|*.*";
                dialog.CheckFileExists = true;
                if (dialog.ShowDialog(this) != DialogResult.OK)
                    return;
                inputBox.Text = dialog.FileName;
                string format = formatBox.SelectedItem.ToString().ToLowerInvariant();
                outputBox.Text = Path.Combine(Path.GetDirectoryName(dialog.FileName),
                    Path.GetFileNameWithoutExtension(dialog.FileName) + " (한국어판)." + format);
            }
        }

        private void OutputBrowseButton_Click(object sender, EventArgs e)
        {
            using (SaveFileDialog dialog = new SaveFileDialog())
            {
                string format = formatBox.SelectedItem.ToString();
                dialog.Title = "한국어판 복사본 저장 위치";
                dialog.Filter = format == "RVZ"
                    ? "RVZ 이미지 (*.rvz)|*.rvz" : "ISO 이미지 (*.iso)|*.iso";
                dialog.DefaultExt = format.ToLowerInvariant();
                dialog.AddExtension = true;
                if (!string.IsNullOrWhiteSpace(outputBox.Text))
                {
                    try {
                        dialog.InitialDirectory =
                            Path.GetDirectoryName(Path.GetFullPath(outputBox.Text));
                        dialog.FileName = Path.GetFileName(outputBox.Text);
                    }
                    catch { }
                }
                if (dialog.ShowDialog(this) == DialogResult.OK)
                    outputBox.Text = dialog.FileName;
            }
        }

        private void FormatBox_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (string.IsNullOrWhiteSpace(outputBox.Text))
                return;
            try {
                outputBox.Text = Path.ChangeExtension(outputBox.Text,
                    formatBox.SelectedItem.ToString().ToLowerInvariant());
            }
            catch { }
        }

        private async void StartButton_Click(object sender, EventArgs e)
        {
            if (cancellation != null)
                return;
            string input = inputBox.Text.Trim();
            string output = outputBox.Text.Trim();
            string format = formatBox.SelectedItem.ToString();
            if (File.Exists(output))
            {
                DialogResult answer = MessageBox.Show(this,
                    "이미 같은 이름의 파일이 있습니다. 성공적으로 검증된 새 파일로 교체할까요?\r\n\r\n" +
                    output, "출력 파일 확인", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
                if (answer != DialogResult.Yes)
                    return;
            }

            SetRunning(true);
            completedOutput = null;
            progressBar.Value = 0;
            logBox.Clear();
            AppendLog("패치 시작");
            cancellation = new CancellationTokenSource();
            CancellationToken token = cancellation.Token;
            Progress<PatchProgress> reporter = new Progress<PatchProgress>(UpdateProgress);
            PatchRequest request = new PatchRequest {
                InputPath = input, OutputPath = output, OutputFormat = format
            };

            try
            {
                PatchWorker worker = new PatchWorker(
                    AppDomain.CurrentDomain.BaseDirectory, reporter, token);
                PatchResult result = await Task.Run(
                    delegate { return worker.Run(request); }, token);
                completedOutput = result.OutputPath;
                openButton.Enabled = true;
                AppendLog("SHA-256: " + result.OutputSha256);
                AppendLog("검증 보고서: " + result.ReportPath);
                MessageBox.Show(this,
                    "한국어판 복사본을 만들고 검증했습니다.\r\n\r\n" + result.OutputPath,
                    "완료", MessageBoxButtons.OK, MessageBoxIcon.Information);
                OpenSelected(result.OutputPath);
            }
            catch (OperationCanceledException)
            {
                statusLabel.Text = "작업을 취소했습니다. 원본 파일은 변경되지 않았습니다.";
                AppendLog("사용자가 작업을 취소했습니다.");
            }
            catch (Exception ex)
            {
                statusLabel.Text = "패치에 실패했습니다.";
                AppendLog("오류: " + ex.Message);
                MessageBox.Show(this, ex.Message, "한국어판 생성 실패",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                if (cancellation != null) {
                    cancellation.Dispose();
                    cancellation = null;
                }
                SetRunning(false);
            }
        }

        private void CancelButton_Click(object sender, EventArgs e)
        {
            if (cancellation != null) {
                cancelButton.Enabled = false;
                statusLabel.Text = "취소하고 임시 파일을 정리하고 있습니다.";
                cancellation.Cancel();
            }
        }
        private void OpenButton_Click(object sender, EventArgs e)
        {
            if (!string.IsNullOrEmpty(completedOutput) && File.Exists(completedOutput))
                OpenSelected(completedOutput);
        }
        private void MainForm_FormClosing(object sender, FormClosingEventArgs e)
        {
            if (cancellation == null)
                return;
            DialogResult answer = MessageBox.Show(this, "패치 작업을 취소하고 창을 닫을까요?",
                "작업 중", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
            if (answer != DialogResult.Yes) {
                e.Cancel = true;
                return;
            }
            cancellation.Cancel();
        }
        private void SetRunning(bool running)
        {
            inputBox.Enabled = !running;
            outputBox.Enabled = !running;
            formatBox.Enabled = !running;
            inputBrowseButton.Enabled = !running;
            outputBrowseButton.Enabled = !running;
            startButton.Enabled = !running;
            cancelButton.Enabled = running;
            if (running) openButton.Enabled = false;
        }
        private void UpdateProgress(PatchProgress update)
        {
            progressBar.Value = Math.Max(progressBar.Minimum,
                Math.Min(progressBar.Maximum, update.Percent));
            statusLabel.Text = update.Status;
            if (!string.IsNullOrWhiteSpace(update.Log))
                AppendLog(update.Log);
        }
        private void AppendLog(string text)
        {
            logBox.AppendText("[" + DateTime.Now.ToString(
                "HH:mm:ss", CultureInfo.InvariantCulture) + "] " +
                text + Environment.NewLine);
            logBox.SelectionStart = logBox.TextLength;
            logBox.ScrollToCaret();
        }
        private static void OpenSelected(string path)
        {
            try {
                Process.Start(new ProcessStartInfo {
                    FileName = "explorer.exe",
                    Arguments = "/select,\"" + path + "\"",
                    UseShellExecute = true
                });
            }
            catch { }
        }
    }

    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }
}
