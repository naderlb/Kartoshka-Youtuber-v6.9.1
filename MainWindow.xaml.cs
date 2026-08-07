using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace KartoshkaYoutuber;

public partial class MainWindow : Window
{
    /// <summary>Pause between playlist items — YouTube rate-limits faster downloads.</summary>
    private const int PauseBetweenItemsSeconds = 8;

    private string? _selectedQuality;
    private readonly Dictionary<string, string> _qualityToFormatId = new();
    private bool _urlIsPlaylist;
    private string _playlistTitle = "playlist";
    private readonly ObservableCollection<PlaylistEntryItem> _playlistEntries = new();
    private readonly List<PlaylistEntryItem> _playlistBackup = new();
    private bool _isDownloading;
    private int _queueTotal;
    private int _queueIndex;

    public MainWindow()
    {
        InitializeComponent();
        InitializeDefaults();
        PlaylistEntriesList.ItemsSource = _playlistEntries;
        ApplyModeUi();
    }

    private bool IsPlaylistMode => ModePlaylistRadio.IsChecked == true;

    private void InitializeDefaults()
    {
        var baseDir = AppContext.BaseDirectory;
        PathTextBox.Text = Path.Combine(baseDir, "download");
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
        return exe;
    }

    private static bool UrlLooksLikePlaylist(string url)
        => url.Contains("list=", StringComparison.OrdinalIgnoreCase)
           || url.Contains("/playlist", StringComparison.OrdinalIgnoreCase);

    private static string StripPlaylistFromUrl(string url)
    {
        try
        {
            var uri = new Uri(url);
            var kept = new List<string>();
            if (!string.IsNullOrEmpty(uri.Query))
            {
                foreach (var part in uri.Query.TrimStart('?').Split('&', StringSplitOptions.RemoveEmptyEntries))
                {
                    var eq = part.IndexOf('=');
                    var key = eq >= 0 ? part[..eq] : part;
                    if (key.Equals("list", StringComparison.OrdinalIgnoreCase) ||
                        key.Equals("index", StringComparison.OrdinalIgnoreCase) ||
                        key.Equals("start_radio", StringComparison.OrdinalIgnoreCase) ||
                        key.Equals("pp", StringComparison.OrdinalIgnoreCase))
                        continue;
                    kept.Add(part);
                }
            }

            var builder = new UriBuilder(uri) { Query = string.Join('&', kept) };
            return builder.Uri.ToString();
        }
        catch
        {
            return url;
        }
    }

    private void DownloadMode_Changed(object sender, RoutedEventArgs e)
    {
        if (!IsInitialized) return;
        ApplyModeUi();
        UpdateDownloadButtonLabel();
    }

    private void ApplyModeUi()
    {
        if (IsPlaylistMode)
        {
            ModeHintText.Text = "Loads the playlist list. Remove songs you don't want, then download the rest one-by-one.";
            var showList = _playlistEntries.Count > 0;
            PlaylistSelectPanel.Visibility = showList ? Visibility.Visible : Visibility.Collapsed;
            PlaylistScroll.Visibility = showList ? Visibility.Visible : Visibility.Collapsed;
            PlaylistMetaText.Visibility = showList || _urlIsPlaylist ? Visibility.Visible : Visibility.Collapsed;
            QueueHintText.Visibility = showList ? Visibility.Visible : Visibility.Collapsed;
            if (showList)
            {
                QueueHintText.Text =
                    $"Remove songs you don't want. Remaining songs download one at a time with a {PauseBetweenItemsSeconds}s pause between each.";
            }
        }
        else
        {
            ModeHintText.Text = "Downloads only the current video from the URL (ignores playlist / Mix).";
            PlaylistSelectPanel.Visibility = Visibility.Collapsed;
            PlaylistScroll.Visibility = Visibility.Collapsed;
            PlaylistMetaText.Visibility = Visibility.Collapsed;
            QueueHintText.Visibility = Visibility.Collapsed;
        }
    }

    private async void GetInfo_Click(object sender, RoutedEventArgs e)
    {
        if (_isDownloading)
        {
            MessageBox.Show("Wait for the current download queue to finish.", "Busy", MessageBoxButton.OK, MessageBoxImage.Information);
            return;
        }

        var url = UrlTextBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(url))
        {
            MessageBox.Show("Please enter a YouTube URL.", "Error", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        _urlIsPlaylist = UrlLooksLikePlaylist(url);

        if (IsPlaylistMode && !_urlIsPlaylist)
        {
            MessageBox.Show(
                "This URL has no playlist. Switch to \"One video\", or paste a URL that contains list= / a playlist link.",
                "Not a playlist",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
            return;
        }

        // One video mode: strip list= so we only fetch the current video
        var infoUrl = url;
        if (!IsPlaylistMode && _urlIsPlaylist)
        {
            infoUrl = StripPlaylistFromUrl(url);
            Log("One video mode — ignoring playlist, using: " + infoUrl);
        }

        Log(IsPlaylistMode ? "Getting playlist info..." : "Getting video info...");
        StatusText.Text = "Getting info...";

        var info = await CallBackendAsync("info", infoUrl);
        if (info is null)
        {
            StatusText.Text = "Failed to get info. See log.";
            return;
        }

        if (info.Value.TryGetProperty("error", out var errProp))
        {
            Log("Backend error: " + (errProp.GetString() ?? "Unknown error"));
            StatusText.Text = "Error getting info.";
            return;
        }

        UpdateVideoInfo(info.Value);
        UpdateQualities(info.Value);
        ApplyModeUi();

        StatusText.Text = IsPlaylistMode
            ? $"Playlist loaded — remove songs you don't want ({_playlistEntries.Count} in queue)."
            : "Info loaded.";
    }

    private void UpdateVideoInfo(JsonElement info)
    {
        var detectedPlaylist = info.GetPropertyOrDefault("is_playlist", false)
            || string.Equals(info.GetPropertyOrDefault("type", "video"), "playlist", StringComparison.OrdinalIgnoreCase);

        _playlistEntries.Clear();
        _playlistBackup.Clear();

        if (IsPlaylistMode && detectedPlaylist)
        {
            InfoHeaderText.Text = "Playlist Information";
            _playlistTitle = info.GetPropertyOrDefault("playlist_title", null)
                             ?? info.GetPropertyOrDefault("title", "playlist")
                             ?? "playlist";
            var count = info.GetPropertyOrDefault("entry_count", 0);
            var isMix = info.GetPropertyOrDefault("is_mix", false);

            TitleText.Text = "Playlist: " + _playlistTitle;
            UploaderText.Text = "Uploader: " + (info.GetPropertyOrDefault("uploader", "-") ?? "-");

            var duration = info.TryGetProperty("duration", out var dProp) && dProp.ValueKind == JsonValueKind.Number
                ? dProp.GetInt32()
                : 0;
            DurationText.Text = FormatDurationLabel("Total duration", duration);
            ViewsText.Text = $"Items: {count}";

            var limit = info.GetPropertyOrDefault("playlist_limit", 0);
            PlaylistMetaText.Text = isMix
                ? (limit > 0
                    ? $"YouTube Mix — first {limit} songs. Remove any you don't want, then Download."
                    : "YouTube Mix. Remove songs you don't want, then Download.")
                : "Remove songs you don't want from the list. The rest will download one-by-one.";
            PlaylistMetaText.Visibility = Visibility.Visible;

            if (info.TryGetProperty("entries", out var entries) && entries.ValueKind == JsonValueKind.Array)
            {
                foreach (var entry in entries.EnumerateArray())
                {
                    var item = CreateEntryFromJson(entry);
                    if (item == null) continue;
                    _playlistEntries.Add(item);
                    _playlistBackup.Add(CloneEntry(item));
                }
            }

            UpdateSelectionCount();
        }
        else
        {
            // Single video (or playlist mode but backend returned one video)
            InfoHeaderText.Text = "Video Information";
            _playlistTitle = "playlist";
            TitleText.Text = "Title: " + (info.GetPropertyOrDefault("title", "-") ?? "-");
            UploaderText.Text = "Uploader: " + (info.GetPropertyOrDefault("uploader", "-") ?? "-");

            var duration = info.TryGetProperty("duration", out var dProp) ? dProp.GetInt32() : 0;
            DurationText.Text = FormatDurationLabel("Duration", duration);

            var views = info.TryGetProperty("view_count", out var vProp) ? vProp.GetInt64() : 0;
            ViewsText.Text = "Views: " + (views > 0 ? views.ToString("N0") : "-");

            PlaylistMetaText.Visibility = Visibility.Collapsed;
        }

        UpdateDownloadButtonLabel();
    }

    private static string FormatDurationLabel(string prefix, int duration)
    {
        if (duration <= 0) return $"{prefix}: -";
        var hours = duration / 3600;
        var minutes = (duration % 3600) / 60;
        var seconds = duration % 60;
        return hours > 0
            ? $"{prefix}: {hours}:{minutes:D2}:{seconds:D2}"
            : $"{prefix}: {minutes}:{seconds:D2}";
    }

    private static PlaylistEntryItem? CreateEntryFromJson(JsonElement entry)
    {
        var idx = entry.GetPropertyOrDefault("index", 0);
        var title = entry.GetPropertyOrDefault("title", "Unknown") ?? "Unknown";
        var entryDuration = entry.GetPropertyOrDefault("duration", 0);
        var entryUrl = entry.GetPropertyOrDefault("url", "") ?? "";
        var id = entry.GetPropertyOrDefault("id", "") ?? "";
        if (string.IsNullOrWhiteSpace(entryUrl) && !string.IsNullOrWhiteSpace(id))
            entryUrl = "https://www.youtube.com/watch?v=" + id;
        if (string.IsNullOrWhiteSpace(entryUrl))
            return null;

        return new PlaylistEntryItem
        {
            Index = idx,
            Title = title,
            Url = entryUrl,
            Duration = entryDuration
        };
    }

    private static PlaylistEntryItem CloneEntry(PlaylistEntryItem src) => new()
    {
        Index = src.Index,
        Title = src.Title,
        Url = src.Url,
        Duration = src.Duration
    };

    private void UpdateSelectionCount()
    {
        SelectionCountText.Text = $"{_playlistEntries.Count} in queue";
        UpdateDownloadButtonLabel();
    }

    private void UpdateDownloadButtonLabel()
    {
        if (IsPlaylistMode)
            DownloadButton.Content = _playlistEntries.Count > 0
                ? $"Download Playlist ({_playlistEntries.Count})"
                : "Download Playlist";
        else
            DownloadButton.Content = "Download Video";
    }

    private void RemovePlaylistItem_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button btn || btn.Tag is not PlaylistEntryItem item)
            return;

        _playlistEntries.Remove(item);
        Log("Removed from queue: " + item.Title);
        UpdateSelectionCount();
        ApplyModeUi();
    }

    private void RestoreAll_Click(object sender, RoutedEventArgs e)
    {
        _playlistEntries.Clear();
        foreach (var item in _playlistBackup)
            _playlistEntries.Add(CloneEntry(item));
        Log($"Restored all {_playlistEntries.Count} songs.");
        UpdateSelectionCount();
        ApplyModeUi();
    }

    private void UpdateQualities(JsonElement info)
    {
        QualitiesPanel.Children.Clear();
        _qualityToFormatId.Clear();
        _selectedQuality = null;

        if (!info.TryGetProperty("formats", out var formats) || formats.ValueKind != JsonValueKind.Array)
        {
            QualityHintText.Text = IsPlaylistMode
                ? "No quality list from the first item — Download will still use Best / selected height."
                : "No quality information available for this video.";
            return;
        }

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

        list.Sort((a, b) => b.height.CompareTo(a.height));

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

        QualityHintText.Text = QualitiesPanel.Children.Count == 0
            ? "No video formats exposed by YouTube/yt-dlp for this video."
            : (IsPlaylistMode
                ? "Quality applies to every song left in the playlist."
                : "Click a quality to select.");
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

    private static string SanitizeFolderName(string name)
    {
        foreach (var c in Path.GetInvalidFileNameChars())
            name = name.Replace(c, '_');
        name = name.Trim(' ', '.');
        return string.IsNullOrWhiteSpace(name) ? "playlist" : name;
    }

    private string ResolveQuality()
    {
        var quality = _selectedQuality ?? "best";
        if (!string.Equals(quality, "best", StringComparison.OrdinalIgnoreCase) &&
            !string.Equals(quality, "worst", StringComparison.OrdinalIgnoreCase))
        {
            var parts = quality.Split('x');
            quality = parts.Length == 2 ? parts[1] : quality;
        }
        return quality;
    }

    private async void Download_Click(object sender, RoutedEventArgs e)
    {
        if (_isDownloading)
            return;

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
        var quality = ResolveQuality();

        if (IsPlaylistMode)
        {
            if (_playlistEntries.Count == 0)
            {
                MessageBox.Show(
                    "Choose Playlist / Mix, click Get Info, then remove songs you don't want. The list cannot be empty.",
                    "Playlist",
                    MessageBoxButton.OK,
                    MessageBoxImage.Information);
                return;
            }

            await DownloadQueueAsync(_playlistEntries.ToList(), quality, format, path);
            return;
        }

        // One video
        var videoUrl = UrlLooksLikePlaylist(url) ? StripPlaylistFromUrl(url) : url;
        Log($"Starting single download: {videoUrl}");
        StatusText.Text = "Downloading...";
        Progress.Value = 0;
        SetDownloadingUi(true);

        try
        {
            var json = await CallBackendRawAsync(
                "download", videoUrl, quality, format, path,
                noPlaylist: true, filenamePrefix: null, noConvert: false, inputPath: null);
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
                StatusText.Text = json.Value.GetPropertyOrDefault("error", "Download failed.") ?? "Download failed.";
            }
        }
        finally
        {
            SetDownloadingUi(false);
        }
    }

    private async Task DownloadQueueAsync(List<PlaylistEntryItem> selected, string quality, string format, string basePath)
    {
        var folder = Path.Combine(basePath, SanitizeFolderName(_playlistTitle));
        Directory.CreateDirectory(folder);

        var isMp3 = string.Equals(format, "mp3", StringComparison.OrdinalIgnoreCase);
        const int maxPasses = 3; // 1 normal + 2 retries for failures
        const int retryPauseSeconds = 15;

        var pending = selected.ToList();
        var okCount = 0;
        var total = selected.Count;

        SetDownloadingUi(true);
        Log($"Playlist queue: {total} song(s). Failed songs will be retried (up to {maxPasses - 1} more passes).");
        StatusText.Text = $"Queued {total} song(s)...";

        try
        {
            for (var pass = 1; pass <= maxPasses && pending.Count > 0; pass++)
            {
                if (pass > 1)
                {
                    Log($"Retry pass {pass}/{maxPasses}: {pending.Count} failed song(s) left. Waiting {retryPauseSeconds}s...");
                    for (var left = retryPauseSeconds; left > 0; left--)
                    {
                        StatusText.Text = $"Retrying failed songs in {left}s ({pending.Count} left)...";
                        await Task.Delay(1000);
                    }
                }

                var stillFailed = new List<PlaylistEntryItem>();
                Task<(bool ok, string? err)>? convertTask = null;
                PlaylistEntryItem? convertItem = null;

                _queueTotal = pending.Count;
                for (var i = 0; i < pending.Count; i++)
                {
                    var item = pending[i];
                    _queueIndex = i + 1;
                    Progress.Value = (double)i / Math.Max(1, pending.Count) * 100;

                    var passLabel = pass == 1 ? "" : $" (retry {pass - 1})";
                    Log($"[{_queueIndex}/{pending.Count}]{passLabel} Downloading: {item.Title}");
                    StatusText.Text = $"Pass {pass}: {_queueIndex}/{pending.Count} — {item.Title}";

                    var prefix = $"{item.Index:D3} - ";
                    var downloadTask = CallBackendRawAsync(
                        "download",
                        item.Url,
                        quality,
                        format,
                        folder,
                        noPlaylist: true,
                        filenamePrefix: prefix,
                        noConvert: isMp3,
                        inputPath: null);

                    JsonElement? json;
                    if (isMp3 && convertTask != null)
                    {
                        await Task.WhenAll(downloadTask, convertTask);
                        var prevConvert = await convertTask;
                        if (prevConvert.ok)
                        {
                            okCount++;
                            Log($"Converted OK: {convertItem?.Title}");
                        }
                        else
                        {
                            if (convertItem != null)
                                stillFailed.Add(convertItem);
                            Log("Convert failed: " + (prevConvert.err ?? "unknown") + $" — will retry: {convertItem?.Title}");
                        }
                        convertTask = null;
                        convertItem = null;
                        json = await downloadTask;
                    }
                    else
                    {
                        json = await downloadTask;
                    }

                    var success = json is not null
                                  && json.Value.TryGetProperty("success", out var okProp)
                                  && okProp.GetBoolean();

                    if (!success)
                    {
                        var err = json?.GetPropertyOrDefault("error", "failed") ?? "failed";
                        Log($"[{_queueIndex}/{pending.Count}] Download failed: {err}");
                        stillFailed.Add(item);
                    }
                    else if (isMp3)
                    {
                        var filepath = json!.Value.GetPropertyOrDefault("filepath", null);
                        if (string.IsNullOrWhiteSpace(filepath) || !File.Exists(filepath))
                        {
                            // Path may use restricted ASCII name — try to find newest matching prefix
                            filepath = FindDownloadedFile(folder, prefix) ?? filepath;
                        }

                        if (string.IsNullOrWhiteSpace(filepath) || !File.Exists(filepath))
                        {
                            Log($"[{_queueIndex}/{pending.Count}] Download ok but file missing — will retry.");
                            stillFailed.Add(item);
                        }
                        else if (filepath.EndsWith(".mp3", StringComparison.OrdinalIgnoreCase))
                        {
                            okCount++;
                            Log($"[{_queueIndex}/{pending.Count}] Already MP3.");
                        }
                        else
                        {
                            Log($"[{_queueIndex}/{pending.Count}] Converting to MP3...");
                            convertTask = ConvertFileAsync(filepath, format);
                            convertItem = item;
                        }
                    }
                    else
                    {
                        okCount++;
                        Log($"[{_queueIndex}/{pending.Count}] Done.");
                    }

                    Progress.Value = (double)_queueIndex / Math.Max(1, pending.Count) * 100;

                    if (i < pending.Count - 1)
                    {
                        var pause = pass == 1 ? PauseBetweenItemsSeconds : Math.Max(PauseBetweenItemsSeconds, 10);
                        for (var left = pause; left > 0; left--)
                        {
                            StatusText.Text = $"Paused {left}s before next...";
                            await Task.Delay(1000);
                        }
                    }
                }

                if (convertTask != null)
                {
                    StatusText.Text = "Finishing MP3 convert...";
                    var last = await convertTask;
                    if (last.ok)
                    {
                        okCount++;
                        Log($"Converted OK: {convertItem?.Title}");
                    }
                    else if (convertItem != null)
                    {
                        stillFailed.Add(convertItem);
                        Log("Convert failed: " + (last.err ?? "unknown") + $" — will retry: {convertItem.Title}");
                    }
                }

                // De-dupe in case an item was added twice
                pending = stillFailed
                    .GroupBy(x => x.Url)
                    .Select(g => g.First())
                    .ToList();

                Log(pass == 1
                    ? $"Pass 1 done. OK so far: {okCount}. Failed: {pending.Count}."
                    : $"Retry pass {pass} done. OK so far: {okCount}. Still failed: {pending.Count}.");
            }

            var finalFailed = pending.Count;
            StatusText.Text = finalFailed == 0
                ? $"Finished: {okCount}/{total} downloaded."
                : $"Finished: {okCount} ok, {finalFailed} still failed after retries (of {total}).";
            Progress.Value = 100;
            Log(StatusText.Text);

            if (finalFailed > 0)
            {
                foreach (var item in pending)
                    Log("Still failed: " + item.Title);
            }
        }
        finally
        {
            SetDownloadingUi(false);
            _queueTotal = 0;
            _queueIndex = 0;
        }
    }

    private static string? FindDownloadedFile(string folder, string prefix)
    {
        try
        {
            if (!Directory.Exists(folder)) return null;
            return Directory.GetFiles(folder)
                .Where(f => Path.GetFileName(f).StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                .OrderByDescending(File.GetLastWriteTimeUtc)
                .FirstOrDefault();
        }
        catch
        {
            return null;
        }
    }

    private async Task<(bool ok, string? err)> ConvertFileAsync(string inputPath, string format)
    {
        try
        {
            var json = await CallBackendRawAsync(
                "convert",
                url: "",
                quality: null,
                format: format,
                path: null,
                noPlaylist: false,
                filenamePrefix: null,
                noConvert: false,
                inputPath: inputPath);

            if (json is null)
                return (false, "no response");
            if (json.Value.TryGetProperty("success", out var ok) && ok.GetBoolean())
            {
                Log("Converted: " + (json.Value.GetPropertyOrDefault("filepath", inputPath) ?? inputPath));
                return (true, null);
            }
            return (false, json.Value.GetPropertyOrDefault("error", "convert failed"));
        }
        catch (Exception ex)
        {
            return (false, ex.Message);
        }
    }

    private void SetDownloadingUi(bool busy)
    {
        _isDownloading = busy;
        DownloadButton.IsEnabled = !busy;
        UrlTextBox.IsEnabled = !busy;
        ModeSingleRadio.IsEnabled = !busy;
        ModePlaylistRadio.IsEnabled = !busy;
    }

    private async Task<JsonElement?> CallBackendAsync(string command, string url)
    {
        try
        {
            return await CallBackendRawAsync(command, url, null, null, null, false, null, false, null);
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
        string? path,
        bool noPlaylist,
        string? filenamePrefix,
        bool noConvert,
        string? inputPath)
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
            psi.ArgumentList.Add(backend);

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

        if (noPlaylist)
            psi.ArgumentList.Add("--no-playlist");

        if (!string.IsNullOrEmpty(filenamePrefix))
        {
            psi.ArgumentList.Add("--filename-prefix");
            psi.ArgumentList.Add(filenamePrefix);
        }

        if (noConvert)
            psi.ArgumentList.Add("--no-convert");

        if (!string.IsNullOrWhiteSpace(inputPath))
        {
            psi.ArgumentList.Add("--input");
            psi.ArgumentList.Add(inputPath);
        }

        using var proc = new Process { StartInfo = psi };

        var outputBuilder = new StringBuilder();
        var errorBuilder = new StringBuilder();

        proc.OutputDataReceived += (_, e) =>
        {
            if (e.Data == null) return;
            lock (outputBuilder) outputBuilder.AppendLine(e.Data);

            try
            {
                using var doc = JsonDocument.Parse(e.Data);
                var root = doc.RootElement;
                if (root.TryGetProperty("type", out var t))
                {
                    var kind = t.GetString();
                    if (kind == "progress")
                    {
                        var pct = root.TryGetProperty("percent", out var p) && p.TryGetDouble(out var pd) ? pd : 0;
                        Dispatcher.Invoke(() =>
                        {
                            if (_queueTotal > 0 && _queueIndex > 0)
                            {
                                var overall = ((_queueIndex - 1) + pct / 100.0) / _queueTotal * 100.0;
                                Progress.Value = Math.Max(0, Math.Min(100, overall));
                                StatusText.Text = $"Downloading {_queueIndex}/{_queueTotal} ({pct:0}%)...";
                            }
                            else
                            {
                                Progress.Value = Math.Max(0, Math.Min(100, pct));
                            }
                        });
                        return; // don't spam the log with every percent tick
                    }

                    if (kind == "status")
                    {
                        var msg = root.GetPropertyOrDefault("message", "") ?? "";
                        Dispatcher.Invoke(() => Log(msg));
                        return;
                    }
                }

                // Final result JSON — log a short summary, not megabytes of playlist dump
                if (root.TryGetProperty("success", out var ok))
                {
                    var shortMsg = ok.GetBoolean()
                        ? (root.GetPropertyOrDefault("message", "OK") ?? "OK")
                        : ("Error: " + (root.GetPropertyOrDefault("error", "failed") ?? "failed"));
                    Dispatcher.Invoke(() => Log(shortMsg));
                    return;
                }

                var hasPlaylist = root.TryGetProperty("is_playlist", out JsonElement _pl);
                var hasFormats = root.TryGetProperty("formats", out JsonElement _fm);
                var hasCount = root.TryGetProperty("entry_count", out JsonElement _ec);
                if ((hasPlaylist || hasFormats || hasCount) && root.TryGetProperty("title", out JsonElement _ti))
                {
                    var title = root.GetPropertyOrDefault("title", "info") ?? "info";
                    var count = root.GetPropertyOrDefault("entry_count", 0);
                    Dispatcher.Invoke(() => Log(count > 0
                        ? $"Loaded playlist: {title} ({count} items)"
                        : $"Loaded: {title}"));
                    return;
                }
            }
            catch
            {
                // not JSON
            }

            // Skip noisy yt-dlp progress lines; keep warnings/errors/strategy notes
            var line = e.Data;
            if (line.Contains("[download]", StringComparison.Ordinal) && line.Contains('%'))
                return;
            if (line.StartsWith("Progress:", StringComparison.Ordinal))
                return;

            Dispatcher.Invoke(() => Log(line));
        };
        proc.ErrorDataReceived += (_, e) =>
        {
            if (e.Data == null) return;
            lock (errorBuilder) errorBuilder.AppendLine(e.Data);
            // Deno / JS runtime warnings are important; still keep them short
            if (e.Data.Contains("JavaScript runtime", StringComparison.OrdinalIgnoreCase))
                Dispatcher.Invoke(() => Log("[WARN] Install Deno for more reliable YouTube downloads (yt-dlp needs a JS runtime)."));
            else if (e.Data.Contains("ERROR", StringComparison.OrdinalIgnoreCase) ||
                     e.Data.Contains("WARNING", StringComparison.OrdinalIgnoreCase))
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
                    if (UrlLooksLikePlaylist(text) && ModePlaylistRadio.IsChecked != true)
                    {
                        // Soft hint only — don't force mode
                        ModeHintText.Text = "URL looks like a playlist / Mix. Switch to \"Playlist / Mix\" if you want the full list.";
                    }
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
        if (Directory.Exists(PathTextBox.Text))
            Process.Start(new ProcessStartInfo("explorer.exe", PathTextBox.Text) { UseShellExecute = true });
    }

    private void Log(string message)
    {
        LogTextBox.AppendText($"[{DateTime.Now:HH:mm:ss}] {message}{Environment.NewLine}");
        LogTextBox.ScrollToEnd();
    }
}

public sealed class PlaylistEntryItem : INotifyPropertyChanged
{
    public int Index { get; set; }
    public string Title { get; set; } = "";
    public string Url { get; set; } = "";
    public int Duration { get; set; }

    public string DisplayLabel
    {
        get
        {
            var dur = Duration > 0 ? $" ({Duration / 60}:{Duration % 60:D2})" : "";
            return $"{Index}. {Title}{dur}";
        }
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    private void OnPropertyChanged([CallerMemberName] string? name = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
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

    public static bool GetPropertyOrDefault(this JsonElement element, string name, bool defaultValue)
    {
        if (!element.TryGetProperty(name, out var prop)) return defaultValue;
        return prop.ValueKind switch
        {
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            _ => defaultValue
        };
    }
}
