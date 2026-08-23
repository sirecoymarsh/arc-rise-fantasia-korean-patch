using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;

namespace ArcRiseFantasiaKoreanRomPatcher
{
    internal sealed class PatchManifest
    {
        public string schema { get; set; }
        public string game_id { get; set; }
        public string patch_title { get; set; }
        public string patch_version { get; set; }
        public SourceContract source_contract { get; set; }
        public PatchTotals totals { get; set; }
        public List<PatchEntry> entries { get; set; }
    }
    internal sealed class SourceContract
    {
        public string main_dol_sha256 { get; set; }
        public int staged_file_count { get; set; }
        public int total_entry_count { get; set; }
    }
    internal sealed class PatchTotals
    {
        public long source_bytes { get; set; }
        public long output_bytes { get; set; }
        public long delta_bytes { get; set; }
    }
    internal sealed class PatchEntry
    {
        public string logical_path { get; set; }
        public string delta_path { get; set; }
        public string source_sha256 { get; set; }
        public string output_sha256 { get; set; }
        public string delta_sha256 { get; set; }
        public long source_size { get; set; }
        public long output_size { get; set; }
        public long delta_size { get; set; }
        public bool roundtrip_verified { get; set; }
    }
    internal sealed class PatchProgress
    {
        public int Percent { get; private set; }
        public string Status { get; private set; }
        public string Log { get; private set; }
        public PatchProgress(int percent, string status, string log)
        {
            Percent = Math.Max(0, Math.Min(100, percent));
            Status = status ?? "";
            Log = log;
        }
    }
    internal sealed class PatchRequest
    {
        public string InputPath { get; set; }
        public string OutputPath { get; set; }
        public string OutputFormat { get; set; }
    }
    internal sealed class PatchResult
    {
        public string OutputPath { get; set; }
        public string ReportPath { get; set; }
        public string OutputSha256 { get; set; }
        public long OutputSize { get; set; }
    }
    internal sealed class ProcessResult
    {
        public int ExitCode { get; set; }
        public string Output { get; set; }
    }

    internal sealed class PatchWorker
    {
        private const string ExpectedManifestSha256 =
            "7CAEED6D8B6B7CAC0EE4C85AB9282154F4944F2A2A4C293818B5F2B62C6B09C2";
        private const string ExpectedSchema = "arf-rom-patcher-delta-v1";
        private const string ExpectedGameId = "RPJJ99";
        private readonly string baseDirectory;
        private readonly string manifestPath;
        private readonly string dolphinToolPath;
        private readonly string xdeltaPath;
        private readonly string witPath;
        private readonly IProgress<PatchProgress> progress;
        private readonly CancellationToken cancellationToken;

        public PatchWorker(string baseDirectory, IProgress<PatchProgress> progress,
            CancellationToken cancellationToken)
        {
            this.baseDirectory = Path.GetFullPath(baseDirectory);
            manifestPath = Path.Combine(this.baseDirectory, "payload", "patch_manifest.json");
            dolphinToolPath = Path.Combine(this.baseDirectory, "tools", "DolphinTool.exe");
            xdeltaPath = Path.Combine(this.baseDirectory, "tools", "xdelta3.exe");
            witPath = Path.Combine(this.baseDirectory, "tools", "wit", "wit.exe");
            this.progress = progress;
            this.cancellationToken = cancellationToken;
        }

        public PatchResult Run(PatchRequest request)
        {
            ValidatePackagedResources();
            ValidateRequest(request);
            PatchManifest manifest = LoadManifest();
            string outputFull = Path.GetFullPath(request.OutputPath);
            string outputDirectory = Path.GetDirectoryName(outputFull);
            string outputFileName = Path.GetFileNameWithoutExtension(outputFull);
            string guid = Guid.NewGuid().ToString("N");
            string workRoot = Path.Combine(outputDirectory, ".arf_ko_patch_" + guid);
            string discRoot = Path.Combine(workRoot, "disc");
            string tempIso = Path.Combine(workRoot, "patched.iso");
            string partialOutput = Path.Combine(outputDirectory,
                "." + outputFileName + "." + guid + ".partial." +
                request.OutputFormat.ToLowerInvariant());

            try
            {
                Report(1, "패치 파일을 점검하고 있습니다.", "패치 매니페스트와 도구 확인 완료");
                EnsureFreeSpace(outputDirectory, request.OutputFormat);
                Directory.CreateDirectory(workRoot);

                Report(3, "원본 게임 정보를 확인하고 있습니다.", null);
                ProcessResult sourceHeader = RunProcess(dolphinToolPath,
                    "header -i " + Quote(request.InputPath), workRoot);
                ValidateHeader(sourceHeader.Output);

                Report(6, "원본 RVZ/ISO의 무결성을 확인하고 있습니다.", "RPJJ99 일본판 확인 완료");
                ValidateDolphinVerification(RunProcess(dolphinToolPath,
                    "verify -i " + Quote(request.InputPath), workRoot).Output);

                Report(10, "원본 게임을 임시 폴더에 풀고 있습니다.", "원본 이미지는 수정하지 않습니다.");
                RunProcess(dolphinToolPath,
                    "extract -i " + Quote(request.InputPath) +
                    " -o " + Quote(discRoot) + " -g -q", workRoot);

                string extractedMain = Path.Combine(discRoot, "DATA", "sys", "main.dol");
                if (!File.Exists(extractedMain))
                    throw new InvalidDataException("추출된 DATA\\sys\\main.dol을 찾을 수 없습니다.");
                string mainSha = HashFile(extractedMain);
                if (!EqualsHash(mainSha, manifest.source_contract.main_dol_sha256))
                    throw new InvalidDataException(
                        "지원하지 않는 일본판입니다. main.dol SHA-256이 기준판과 다릅니다.\r\n" +
                        "예상: " + manifest.source_contract.main_dol_sha256 + "\r\n실제: " + mainSha);

                Report(20, "한국어 패치를 적용하고 있습니다.", "원본 파일 722개를 해시로 대조합니다.");
                ApplyDeltas(manifest, discRoot, workRoot);

                Report(67, "한국어판 ISO를 조립하고 있습니다.", "파일 패치 적용 및 출력 해시 검증 완료");
                RunProcess(witPath, "copy " + Quote(discRoot) + " " + Quote(tempIso) +
                    " --iso --psel data --overwrite --quiet", workRoot);
                if (!File.Exists(tempIso) ||
                    new FileInfo(tempIso).Length < 1024L * 1024L * 1024L)
                    throw new InvalidDataException("WIT가 유효한 ISO를 만들지 못했습니다.");

                string imageToVerify;
                if (request.OutputFormat.Equals("RVZ", StringComparison.OrdinalIgnoreCase))
                {
                    Report(82, "ISO를 RVZ로 압축하고 있습니다.", "Zstandard 레벨 5");
                    RunProcess(dolphinToolPath, "convert -i " + Quote(tempIso) +
                        " -o " + Quote(partialOutput) +
                        " -f rvz -b 131072 -c zstd -l 5", workRoot);
                    imageToVerify = partialOutput;
                }
                else
                {
                    TryDeleteFile(partialOutput);
                    File.Move(tempIso, partialOutput);
                    imageToVerify = partialOutput;
                }

                Report(92, "완성된 게임 이미지를 검증하고 있습니다.", null);
                ProcessResult outputHeader = RunProcess(dolphinToolPath,
                    "header -i " + Quote(imageToVerify), workRoot);
                ValidateHeader(outputHeader.Output);
                ValidateDolphinVerification(RunProcess(dolphinToolPath,
                    "verify -i " + Quote(imageToVerify), workRoot).Output);

                cancellationToken.ThrowIfCancellationRequested();
                if (File.Exists(outputFull))
                    File.Delete(outputFull);
                File.Move(partialOutput, outputFull);

                Report(97, "최종 SHA-256을 계산하고 있습니다.", null);
                string outputSha = HashFile(outputFull);
                long outputSize = new FileInfo(outputFull).Length;
                string reportPath = outputFull + ".patch-report.json";
                WriteReport(reportPath, request, manifest, sourceHeader.Output,
                    outputHeader.Output, outputSha, outputSize);
                Report(100, "한국어판 복사본 생성이 완료되었습니다.", "완료: " + outputFull);
                return new PatchResult {
                    OutputPath = outputFull, ReportPath = reportPath,
                    OutputSha256 = outputSha, OutputSize = outputSize
                };
            }
            catch
            {
                TryDeleteFile(partialOutput);
                throw;
            }
            finally
            {
                TryDeleteDirectory(workRoot);
            }
        }

        private void ValidatePackagedResources()
        {
            foreach (string path in new[] { manifestPath, dolphinToolPath, xdeltaPath, witPath })
                if (!File.Exists(path))
                    throw new FileNotFoundException("패처 구성 파일이 없습니다.", path);
            string actual = HashFile(manifestPath);
            if (!EqualsHash(actual, ExpectedManifestSha256))
                throw new InvalidDataException("patch_manifest.json이 손상되었거나 다른 버전입니다.\r\n" +
                    "예상: " + ExpectedManifestSha256 + "\r\n실제: " + actual);
        }

        private static void ValidateRequest(PatchRequest request)
        {
            if (request == null)
                throw new ArgumentNullException("request");
            if (string.IsNullOrWhiteSpace(request.InputPath) || !File.Exists(request.InputPath))
                throw new FileNotFoundException("원본 RVZ/ISO 파일을 찾을 수 없습니다.", request.InputPath);
            string extension = Path.GetExtension(request.InputPath);
            if (!extension.Equals(".rvz", StringComparison.OrdinalIgnoreCase) &&
                !extension.Equals(".iso", StringComparison.OrdinalIgnoreCase))
                throw new ArgumentException("입력 파일은 .rvz 또는 .iso여야 합니다.");
            if (!request.OutputFormat.Equals("RVZ", StringComparison.OrdinalIgnoreCase) &&
                !request.OutputFormat.Equals("ISO", StringComparison.OrdinalIgnoreCase))
                throw new ArgumentException("출력 형식은 RVZ 또는 ISO여야 합니다.");
            if (string.IsNullOrWhiteSpace(request.OutputPath))
                throw new ArgumentException("한국어판 저장 위치를 지정하세요.");
            if (request.InputPath.IndexOf('"') >= 0 || request.OutputPath.IndexOf('"') >= 0)
                throw new ArgumentException("파일 경로에 큰따옴표(\")는 사용할 수 없습니다.");
            string inputFull = Path.GetFullPath(request.InputPath);
            string outputFull = Path.GetFullPath(request.OutputPath);
            if (inputFull.Equals(outputFull, StringComparison.OrdinalIgnoreCase))
                throw new ArgumentException("원본과 출력 파일은 서로 다른 경로여야 합니다.");
            string directory = Path.GetDirectoryName(outputFull);
            if (string.IsNullOrEmpty(directory))
                throw new ArgumentException("출력 폴더를 확인할 수 없습니다.");
            Directory.CreateDirectory(directory);
        }

        private PatchManifest LoadManifest()
        {
            JavaScriptSerializer serializer = new JavaScriptSerializer();
            serializer.MaxJsonLength = int.MaxValue;
            PatchManifest manifest = serializer.Deserialize<PatchManifest>(
                File.ReadAllText(manifestPath, Encoding.UTF8));
            if (manifest == null || manifest.schema != ExpectedSchema)
                throw new InvalidDataException("지원하지 않는 패치 매니페스트 형식입니다.");
            if (manifest.game_id != ExpectedGameId)
                throw new InvalidDataException("패치의 게임 ID가 RPJJ99가 아닙니다.");
            if (manifest.source_contract == null || manifest.entries == null)
                throw new InvalidDataException("패치 매니페스트의 필수 필드가 없습니다.");
            if (manifest.entries.Count != 722 ||
                manifest.entries.Count != manifest.source_contract.total_entry_count ||
                manifest.source_contract.staged_file_count != 721)
                throw new InvalidDataException("패치 매니페스트의 파일 수가 올바르지 않습니다.");
            if (manifest.entries.Any(delegate(PatchEntry e) { return !e.roundtrip_verified; }))
                throw new InvalidDataException("왕복 검증되지 않은 델타가 포함되어 있습니다.");
            return manifest;
        }

        private void ApplyDeltas(PatchManifest manifest, string discRoot, string workRoot)
        {
            string fullDiscRoot = EnsureTrailingSeparator(Path.GetFullPath(discRoot));
            string fullBase = EnsureTrailingSeparator(Path.GetFullPath(Path.Combine(baseDirectory, "payload")));
            int count = manifest.entries.Count;
            for (int index = 0; index < count; index++)
            {
                cancellationToken.ThrowIfCancellationRequested();
                PatchEntry entry = manifest.entries[index];
                string source = ResolveUnder(fullDiscRoot, entry.logical_path);
                string delta = ResolveUnder(fullBase, entry.delta_path);
                string partial = source + ".arfpartial";
                CheckSize(source, entry.source_size, entry.logical_path + ": 원본");
                CheckSize(delta, entry.delta_size, entry.delta_path + ": 델타");
                if (!EqualsHash(HashFile(source), entry.source_sha256))
                    throw new InvalidDataException(entry.logical_path + ": 원본 SHA-256이 기준판과 다릅니다.");
                if (!EqualsHash(HashFile(delta), entry.delta_sha256))
                    throw new InvalidDataException(entry.delta_path + ": 델타가 손상되었습니다.");
                TryDeleteFile(partial);
                RunProcess(xdeltaPath, "-d -f -s " + Quote(source) + " " +
                    Quote(delta) + " " + Quote(partial), workRoot);
                CheckSize(partial, entry.output_size, entry.logical_path + ": 패치 출력");
                if (!EqualsHash(HashFile(partial), entry.output_sha256))
                    throw new InvalidDataException(entry.logical_path + ": 패치 출력 검증에 실패했습니다.");
                File.Delete(source);
                File.Move(partial, source);
                int done = index + 1;
                int percent = 20 + (int)Math.Floor(done * 45.0 / count);
                Report(percent, "한국어 패치를 적용하고 있습니다. (" + done + "/" + count + ")",
                    done == 1 || done % 25 == 0 || done == count ? entry.logical_path : null);
            }
        }

        private static void CheckSize(string path, long expected, string label)
        {
            if (!File.Exists(path))
                throw new FileNotFoundException(label + " 파일을 찾을 수 없습니다.", path);
            if (new FileInfo(path).Length != expected)
                throw new InvalidDataException(label + " 파일 크기가 다릅니다.");
        }

        private static void ValidateHeader(string text)
        {
            string value = text ?? "";
            if (value.IndexOf("Game ID: RPJJ99", StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException("게임 ID가 RPJJ99가 아닙니다.");
            if (value.IndexOf("Region: NTSC-J", StringComparison.OrdinalIgnoreCase) < 0 ||
                value.IndexOf("Country: Japan", StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException("일본판(NTSC-J) 이미지가 아닙니다.");
            if (value.IndexOf("Revision: 0", StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException("지원하지 않는 디스크 리비전입니다.");
        }

        private static void ValidateDolphinVerification(string text)
        {
            string value = text ?? "";
            if (value.IndexOf("Problems Found:", StringComparison.OrdinalIgnoreCase) < 0 ||
                value.IndexOf("Problems Found: No", StringComparison.OrdinalIgnoreCase) >= 0)
                return;

            string[] allowed = {
                "The update partition is missing.",
                "The DATA partition is not correctly signed."
            };
            List<string> summaries = new List<string>();
            foreach (string raw in value.Split(new[] { "\r\n", "\n" },
                StringSplitOptions.RemoveEmptyEntries))
            {
                string line = raw.Trim();
                if (line.StartsWith("Summary:", StringComparison.OrdinalIgnoreCase))
                    summaries.Add(line.Substring("Summary:".Length).Trim());
            }
            if (summaries.Count == 0 || summaries.Any(delegate(string summary) {
                return !allowed.Contains(summary, StringComparer.OrdinalIgnoreCase);
            }))
                throw new InvalidDataException("DolphinTool 무결성 검증에서 예상하지 못한 문제가 발견되었습니다.\r\n" +
                    Tail(value, 1200));
        }

        private static void EnsureFreeSpace(string directory, string format)
        {
            DriveInfo drive = new DriveInfo(Path.GetPathRoot(Path.GetFullPath(directory)));
            long required = format.Equals("RVZ", StringComparison.OrdinalIgnoreCase)
                ? 15L * 1024L * 1024L * 1024L
                : 11L * 1024L * 1024L * 1024L;
            if (drive.AvailableFreeSpace < required)
                throw new IOException("출력 드라이브의 여유 공간이 부족합니다.\r\n필요: 약 " +
                    FormatBytes(required) + "\r\n현재: " + FormatBytes(drive.AvailableFreeSpace));
        }

        private ProcessResult RunProcess(string executable, string arguments, string workingDirectory)
        {
            cancellationToken.ThrowIfCancellationRequested();
            ProcessStartInfo info = new ProcessStartInfo {
                FileName = executable, Arguments = arguments,
                WorkingDirectory = workingDirectory, UseShellExecute = false,
                CreateNoWindow = true, RedirectStandardOutput = true,
                RedirectStandardError = true, StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8
            };
            using (Process process = new Process())
            {
                process.StartInfo = info;
                if (!process.Start())
                    throw new InvalidOperationException("도구 실행에 실패했습니다: " + executable);
                Task<string> stdout = process.StandardOutput.ReadToEndAsync();
                Task<string> stderr = process.StandardError.ReadToEndAsync();
                while (!process.WaitForExit(250))
                {
                    if (cancellationToken.IsCancellationRequested)
                    {
                        try { process.Kill(); } catch { }
                        cancellationToken.ThrowIfCancellationRequested();
                    }
                }
                Task.WaitAll(stdout, stderr);
                string output = (stdout.Result ?? "") + (stderr.Result ?? "");
                if (process.ExitCode != 0)
                    throw new InvalidOperationException(Path.GetFileName(executable) +
                        " 실행 실패 (" + process.ExitCode + ")\r\n" + Tail(output, 2400));
                return new ProcessResult { ExitCode = process.ExitCode, Output = output };
            }
        }

        private string HashFile(string path)
        {
            using (SHA256 sha = SHA256.Create())
            using (FileStream stream = new FileStream(path, FileMode.Open, FileAccess.Read,
                FileShare.Read, 8 * 1024 * 1024, FileOptions.SequentialScan))
            {
                byte[] buffer = new byte[8 * 1024 * 1024];
                int read;
                while ((read = stream.Read(buffer, 0, buffer.Length)) > 0)
                {
                    cancellationToken.ThrowIfCancellationRequested();
                    sha.TransformBlock(buffer, 0, read, null, 0);
                }
                sha.TransformFinalBlock(new byte[0], 0, 0);
                return ToHex(sha.Hash);
            }
        }

        private void WriteReport(string path, PatchRequest request, PatchManifest manifest,
            string sourceHeader, string outputHeader, string outputSha, long outputSize)
        {
            Dictionary<string, object> report = new Dictionary<string, object>();
            report["schema"] = "arf-rom-patcher-result-v1";
            report["valid"] = true;
            report["completed_at"] = DateTimeOffset.Now.ToString("o", CultureInfo.InvariantCulture);
            report["patch_version"] = manifest.patch_version;
            report["game_id"] = manifest.game_id;
            report["input_path"] = Path.GetFullPath(request.InputPath);
            report["input_container"] = Path.GetExtension(request.InputPath).TrimStart('.').ToUpperInvariant();
            report["output_path"] = Path.GetFullPath(request.OutputPath);
            report["output_container"] = request.OutputFormat.ToUpperInvariant();
            report["output_size"] = outputSize;
            report["output_sha256"] = outputSha;
            report["patch_manifest_sha256"] = ExpectedManifestSha256;
            report["patched_entries"] = manifest.entries.Count;
            report["source_header_text"] = sourceHeader.Trim();
            report["output_header_text"] = outputHeader.Trim();
            report["source_image_modified"] = false;
            report["output_is_a_separate_copy"] = true;
            JavaScriptSerializer serializer = new JavaScriptSerializer();
            serializer.MaxJsonLength = int.MaxValue;
            File.WriteAllText(path, serializer.Serialize(report) + Environment.NewLine,
                new UTF8Encoding(false));
        }

        private static string ResolveUnder(string root, string relative)
        {
            if (string.IsNullOrWhiteSpace(relative))
                throw new InvalidDataException("매니페스트에 빈 경로가 있습니다.");
            string full = Path.GetFullPath(Path.Combine(root,
                relative.Replace('/', Path.DirectorySeparatorChar)));
            if (!full.StartsWith(root, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("매니페스트 경로가 루트를 벗어납니다: " + relative);
            return full;
        }
        private static string EnsureTrailingSeparator(string path)
        {
            return path.EndsWith(Path.DirectorySeparatorChar.ToString(), StringComparison.Ordinal)
                ? path : path + Path.DirectorySeparatorChar;
        }
        private static string Quote(string value)
        {
            return "\"" + value.Replace("\"", "\\\"") + "\"";
        }
        private static bool EqualsHash(string left, string right)
        {
            return string.Equals(left, right, StringComparison.OrdinalIgnoreCase);
        }
        private static string ToHex(byte[] bytes)
        {
            StringBuilder result = new StringBuilder(bytes.Length * 2);
            foreach (byte value in bytes)
                result.Append(value.ToString("X2", CultureInfo.InvariantCulture));
            return result.ToString();
        }
        private void Report(int percent, string status, string log)
        {
            if (progress != null)
                progress.Report(new PatchProgress(percent, status, log));
        }
        private static string Tail(string value, int length)
        {
            if (string.IsNullOrEmpty(value) || value.Length <= length)
                return value ?? "";
            return value.Substring(value.Length - length);
        }
        private static string FormatBytes(long value)
        {
            double size = value;
            string[] units = { "B", "KiB", "MiB", "GiB", "TiB" };
            int unit = 0;
            while (size >= 1024.0 && unit < units.Length - 1) { size /= 1024.0; unit++; }
            return size.ToString(unit == 0 ? "0" : "0.00", CultureInfo.InvariantCulture) +
                " " + units[unit];
        }
        private static void TryDeleteFile(string path)
        {
            try { if (!string.IsNullOrEmpty(path) && File.Exists(path)) File.Delete(path); }
            catch { }
        }
        private static void TryDeleteDirectory(string path)
        {
            for (int attempt = 0; attempt < 3; attempt++)
            {
                try
                {
                    if (!string.IsNullOrEmpty(path) && Directory.Exists(path))
                        Directory.Delete(path, true);
                    return;
                }
                catch { Thread.Sleep(500); }
            }
        }
    }
}
