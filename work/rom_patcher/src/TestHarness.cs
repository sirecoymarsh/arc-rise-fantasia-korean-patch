using System;
using System.IO;
using System.Threading;

namespace ArcRiseFantasiaKoreanRomPatcher
{
    internal static class TestHarness
    {
        private static int Main(string[] args)
        {
            if (args.Length != 4)
            {
                Console.Error.WriteLine(
                    "usage: PatcherE2E.exe <package-dir> <input.rvz|iso> <output.rvz|iso> <RVZ|ISO>");
                return 2;
            }
            try
            {
                Progress<PatchProgress> progress = new Progress<PatchProgress>(
                    delegate(PatchProgress p)
                    {
                        Console.WriteLine(
                            "[{0,3}%] {1}{2}",
                            p.Percent,
                            p.Status,
                            string.IsNullOrEmpty(p.Log) ? "" : " :: " + p.Log);
                    });
                PatchWorker worker = new PatchWorker(
                    Path.GetFullPath(args[0]), progress, CancellationToken.None);
                PatchResult result = worker.Run(new PatchRequest
                {
                    InputPath = Path.GetFullPath(args[1]),
                    OutputPath = Path.GetFullPath(args[2]),
                    OutputFormat = args[3]
                });
                Console.WriteLine("OUTPUT=" + result.OutputPath);
                Console.WriteLine("SHA256=" + result.OutputSha256);
                Console.WriteLine("SIZE=" + result.OutputSize);
                Console.WriteLine("REPORT=" + result.ReportPath);
                return 0;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine(ex.ToString());
                return 1;
            }
        }
    }
}
