using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Microsoft.Win32;

namespace KartoshkaYoutuber;

public partial class MainWindow : Window
{
    private string? _selectedQuality; // e.g. "1920x1080"
    private readonly Dictionary<string, string> _qualityToFormatId = new();

    public MainWindow()
    {
        InitializeComponent();
        InitializeDefaults();
    }

    private void InitializeDefaults()
    {
        // Default download folder: "download" next to the exe
        var baseDir = AppContext.BaseDirectory;
        var downloadDir = Path.Combine(baseDir, "download");
        PathTextBox.Text = downloadDir;
    }

    private string GetBackendPath(out bool usePython)
    {
        var baseDir = AppContext.BaseDirectory;
        var exe = Path.Combine(baseDir, "kartoshka-backend.exe");
        var py = Path.Combine(baseDir, "backend.py");

        if (File.Exists(exe))
        {
            usePython = false;
            return exe;
        }

        if (File.Exists(py))
        {
            usePython = true;
            return py;
        }

        usePython = false;
        return exe; // will fail with clear error
    }

    private async void GetInfo_Click(object sender, RoutedEventArgs e)
    {
        var url = UrlTextBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(url))
        {
            MessageBox.Show("Please enter a YouTube URL.", "Error", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        Log("Getting video info...");
        StatusText.Text = "Getting video info...";

        var info = await CallBackendAsync("info", url);
        if (info is null)
        {
            StatusText.Text = "Failed to get info. See log.";
            return;
        }

        if (info.Value.TryGetProperty("error", out var errProp))
        {
            var err = errProp.GetString() ?? "Unknown error";
            Log("Backend error: " + err);
            StatusText.Text = "Error getting info.";
            return;
        }

        UpdateVideoInfo(info.Value);
        UpdateQualities(info.Value);
        StatusText.Text = "Info loaded.";
    }

    private void UpdateVideoInfo(JsonElement info)
    {
        TitleText.Text = "Title: " + (info.GetPropertyOrDefault("title", "-") ?? "-");
        UploaderText.Text = "Uploader: " + (info.GetPropertyOrDefault("uploader", "-") ?? "-");

        var duration = info.TryGetProperty("duration", out var dProp) ? dProp.GetInt32() : 0;
        var minutes = duration / 60;
        var seconds = duration % 60;
        DurationText.Text = $"Duration: {minutes}:{seconds:D2}";

        var views = info.TryGetProperty("view_count", out var vProp) ? vProp.GetInt64() : 0;
        ViewsText.Text = "Views: " + (views > 0 ? views.ToString("N0") : "-");
    }

    private void UpdateQualities(JsonElement info)
    {
        QualitiesPanel.Children.Clear();
        _qualityToFormatId.Clear();
        _selectedQuality = null;

        if (!info.TryGetProperty("formats", out var formats) || formats.ValueKind != JsonValueKind.Array)
        {
            QualityHintText.Text = "No quality information available for this video.";
            return;
        }

        // Collect unique resolutions, prefer higher quality first
        var list = new List<(string resolution, int height, string formatId)>();
        foreach (var fmt in formats.EnumerateArray())
        {
            var vcodec = fmt.GetPropertyOrDefault("vcodec", "");
            if (string.Equals(vcodec, "none", StringComparison.OrdinalIgnoreCase))
                continue;

            var resolution = fmt.GetPropertyOrDefault("resolution", "") ?? "";
            if (string.IsNullOrWhiteSpace(resolution))
            {
                var w = fmt.GetPropertyOrDefault("width", 0);
                var h = fmt.GetPropertyOrDefault("height", 0);
                if (w > 0 && h > 0)
                    resolution = $"{w}x{h}";
            }

            if (string.IsNullOrWhiteSpace(resolution))
                continue;

            var height = fmt.GetPropertyOrDefault("height", 0);
            var formatId = fmt.GetPropertyOrDefault("format_id", "");
            if (string.IsNullOrWhiteSpace(formatId))
                continue;

            list.Add((resolution, height, formatId));
        }

        if (list.Count == 0)
        {
            QualityHintText.Text = "No video formats exposed by YouTube/yt-dlp for this video.";
            return;
        }

        list.Sort((a, b) => b.height.CompareTo(a.height)); // highest first

        foreach (var item in list)
        {
            if (_qualityToFormatId.ContainsKey(item.resolution))
                continue;

            _qualityToFormatId[item.resolution] = item.formatId;

            var btn = new Button
            {
                Content = item.resolution,
                Margin = new Thickness(0, 0, 8, 8),
                Padding = new Thickness(10, 4, 10, 4),
                Background = new SolidColorBrush(Color.FromRgb(55, 65, 81)),
                Foreground = new SolidColorBrush(Colors.White),
                BorderBrush = new SolidColorBrush(Color.FromRgb(75, 85, 99)),
                Tag = item.resolution
            };
            btn.Click += QualityButton_Click;
            QualitiesPanel.Children.Add(btn);
        }

        if (QualitiesPanel.Children.Count == 0)
        {
            QualityHintText.Text = "No video formats exposed by YouTube/yt-dlp for this video.";
        }
        else
        {
            QualityHintText.Text = "Click a quality to select.";
        }
    }

    private void QualityButton_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button btn || btn.Tag is not string res)
            return;

        _selectedQuality = res;

        foreach (var child in QualitiesPanel.Children)
        {
            if (child is Button b)
            {
                var isSelected = Equals(b.Tag, res);
                b.Background = new SolidColorBrush(isSelected ? Color.FromRgb(37, 99, 235) : Color.FromRgb(55, 65, 81));
                b.BorderBrush = new SolidColorBrush(isSelected ? Color.FromRgb(37, 99, 235) : Color.FromRgb(75, 85, 99));
            }
        }

        Log($"Selected quality: {res}");
    }

    private async void Download_Click(object sender, RoutedEventArgs e)
    {
        var url = UrlTextBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(url))
        {
            MessageBox.Show("Please enter a YouTube URL.", "Error", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var path = PathTextBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(path))
        {
            MessageBox.Show("Please choose a download folder.", "Error", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        Directory.CreateDirectory(path);

        var format = ((ComboBoxItem)FormatCombo.SelectedItem!).Content!.ToString()!.ToLowerInvariant();

        var quality = _selectedQuality ?? "best";
        if (!string.Equals(quality, "best", StringComparison.OrdinalIgnoreCase) &&
            !string.Equals(quality, "worst", StringComparison.OrdinalIgnoreCase))
        {
            // Convert "1920x1080" -> "1080" for backend logic
            var parts = quality.Split('x');
            quality = parts.Length == 2 ? parts[1] : quality;
        }

        Log($"Starting download: {url}");
        StatusText.Text = "Downloading...";
        Progress.Value = 0;

        var json = await CallBackendRawAsync("download", url, quality, format, path);
        if (json is null)
        {
            StatusText.Text = "Download failed (no response).";
            return;
        }

        if (json.Value.TryGetProperty("success", out var okProp) && okProp.GetBoolean())
        {
            StatusText.Text = json.Value.GetPropertyOrDefault("message", "Download completed!")!;
            Progress.Value = 100;
        }
        else
        {
            var err = json.Value.GetPropertyOrDefault("error", "Download failed.") ?? "Download failed.";
            StatusText.Text = err;
        }
    }

    private async Task<JsonElement?> CallBackendAsync(string command, string url)
    {
        try
        {
            return await CallBackendRawAsync(command, url, null, null, null);
        }
        catch (Exception ex)
        {
            Log("Error calling backend: " + ex.Message);
            return null;
        }
    }

    private async Task<JsonElement?> CallBackendRawAsync(
        string command,
        string url,
        string? quality,
        string? format,
        string? path)
    {
        bool usePython;
        var backend = GetBackendPath(out usePython);
        if (!File.Exists(backend))
        {
            MessageBox.Show("Backend not found. Make sure kartoshka-backend.exe or backend.py is next to the GUI.", "Error",
                MessageBoxButton.OK, MessageBoxImage.Error);
            return null;
        }

        var psi = new ProcessStartInfo
        {
            FileName = usePython ? "python" : backend,
            WorkingDirectory = Path.GetDirectoryName(backend)!,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        if (usePython)
        {
            psi.ArgumentList.Add(backend);
        }

        psi.ArgumentList.Add("--command");
        psi.ArgumentList.Add(command);
        if (!string.IsNullOrWhiteSpace(url))
        {
            psi.ArgumentList.Add("--url");
            psi.ArgumentList.Add(url);
        }

        if (!string.IsNullOrWhiteSpace(quality))
        {
            psi.ArgumentList.Add("--quality");
            psi.ArgumentList.Add(quality);
        }

        if (!string.IsNullOrWhiteSpace(format))
        {
            psi.ArgumentList.Add("--format");
            psi.ArgumentList.Add(format);
        }

        if (!string.IsNullOrWhiteSpace(path))
        {
            psi.ArgumentList.Add("--path");
            psi.ArgumentList.Add(path);
        }

        using var proc = new Process { StartInfo = psi };

        var outputBuilder = new StringBuilder();
        var errorBuilder = new StringBuilder();

        proc.OutputDataReceived += (_, e) =>
        {
            if (e.Data == null) return;
            lock (outputBuilder) outputBuilder.AppendLine(e.Data);
            Dispatcher.Invoke(() => Log(e.Data));
        };
        proc.ErrorDataReceived += (_, e) =>
        {
            if (e.Data == null) return;
            lock (errorBuilder) errorBuilder.AppendLine(e.Data);
            Dispatcher.Invoke(() => Log("[ERR] " + e.Data));
        };

        proc.Start();
        proc.BeginOutputReadLine();
        proc.BeginErrorReadLine();

        await proc.WaitForExitAsync();

        var combined = outputBuilder.ToString().Trim();
        if (string.IsNullOrWhiteSpace(combined))
            combined = errorBuilder.ToString().Trim();

        if (string.IsNullOrWhiteSpace(combined))
            return null;

        // Take last non-empty line as JSON (backend prints debug + JSON)
        var lines = combined.Split('\n', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
        for (var i = lines.Length - 1; i >= 0; i--)
        {
            try
            {
                var doc = JsonDocument.Parse(lines[i]);
                return doc.RootElement.Clone();
            }
            catch
            {
                // continue
            }
        }

        return null;
    }

    private void Paste_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            if (Clipboard.ContainsText())
            {
                var text = Clipboard.GetText().Trim();
                if (!string.IsNullOrWhiteSpace(text))
                {
                    UrlTextBox.Text = text;
                    Log("URL pasted from clipboard.");
                }
            }
        }
        catch
        {
            // ignore
        }
    }

    private void Browse_Click(object sender, RoutedEventArgs e)
    {
        var dlg = new Microsoft.Win32.OpenFileDialog(); // placeholder: we won't actually use it
        // Simple fallback: open the folder in Explorer and let the user paste path manually.
        if (Directory.Exists(PathTextBox.Text))
            Process.Start(new ProcessStartInfo("explorer.exe", PathTextBox.Text) { UseShellExecute = true });
    }

    private void Log(string message)
    {
        LogTextBox.AppendText($"[{DateTime.Now:HH:mm:ss}] {message}{Environment.NewLine}");
        LogTextBox.ScrollToEnd();
    }
}

internal static class JsonExtensions
{
    public static string? GetPropertyOrDefault(this JsonElement element, string name, string? defaultValue)
    {
        return element.TryGetProperty(name, out var prop) && prop.ValueKind != JsonValueKind.Null
            ? prop.ToString()
            : defaultValue;
    }

    public static int GetPropertyOrDefault(this JsonElement element, string name, int defaultValue)
    {
        if (!element.TryGetProperty(name, out var prop)) return defaultValue;
        return prop.ValueKind switch
        {
            JsonValueKind.Number when prop.TryGetInt32(out var i) => i,
            _ => defaultValue
        };
    }

    public static long GetPropertyOrDefault(this JsonElement element, string name, long defaultValue)
    {
        if (!element.TryGetProperty(name, out var prop)) return defaultValue;
        return prop.ValueKind switch
        {
            JsonValueKind.Number when prop.TryGetInt64(out var i) => i,
            _ => defaultValue
        };
    }
}

