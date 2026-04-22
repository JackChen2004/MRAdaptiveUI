using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;

public class Logger : MonoBehaviour
{
    [Header("References")]
    public SimonGameManager gameManager;
    public Camera gazeCamera;
    public RectTransform uiRect;
    public Transform avatarHead;

    [Header("Metadata")]
    public string participantId = "P001";
    public int avatarNumber = 1;

    [Header("Gaze Sampling")]
    public float sampleIntervalSeconds = 1.0f;
    public float avatarHitRadius = 0.20f;
    [Range(0f, 0.45f)]
    public float uiInnerPaddingPercent = 0.15f; 

    float _gameStartTime = -1f;
    float _nextSampleTime = -1f;
    bool _sessionActive;
    readonly List<string> _gazeSamples = new List<string>();

    void Reset()
    {
        if (!gazeCamera) gazeCamera = Camera.main;
    }

    void Awake()
    {
        if (!gazeCamera) gazeCamera = Camera.main;
    }

    void OnEnable()
    {
        if (gameManager == null) return;
        gameManager.OnGameStarted += HandleGameStarted;
        gameManager.OnGameCompleted += HandleGameCompleted;
        gameManager.OnGameFailed += HandleGameFailed;
    }

    void OnDisable()
    {
        if (gameManager == null) return;
        gameManager.OnGameStarted -= HandleGameStarted;
        gameManager.OnGameCompleted -= HandleGameCompleted;
        gameManager.OnGameFailed -= HandleGameFailed;
    }

    void Update()
    {
        if (!_sessionActive) return;
        if (!gazeCamera) return;

        float interval = Mathf.Max(0.1f, sampleIntervalSeconds);
        while (Time.time >= _nextSampleTime)
        {
            int second = Mathf.Max(0, Mathf.FloorToInt(_nextSampleTime - _gameStartTime));
            _gazeSamples.Add($"{second},{GetCurrentGazeLabel()}");
            _nextSampleTime += interval;
        }
    }

    void HandleGameStarted()
    {
        _gameStartTime = Time.time;
        _nextSampleTime = _gameStartTime; // include second 0
        _sessionActive = true;
        _gazeSamples.Clear();
    }

    // State of the game result
    void HandleGameCompleted(int _)
    {
        FlushSessionLog("SUCCESS");
    }

    void HandleGameFailed(int _)
    {
        FlushSessionLog("FAILED");
    }

    // Pause would be triggered only if user quits the experiment.
    void OnApplicationPause(bool pauseStatus)
    {
        if (pauseStatus)
            FlushSessionLog("APP_EXIT");
    }

    void OnApplicationQuit()
    {
        FlushSessionLog("APP_EXIT");
    }

    // Gazing data collection
    string GetCurrentGazeLabel()
    {
        Ray ray = new Ray(gazeCamera.transform.position, gazeCamera.transform.forward);

        bool uiHit = TryGetUiHitDistance(ray, out float uiDist);
        bool avatarHit = TryGetAvatarHitDistance(ray, out float avatarDist);

        if (uiHit && avatarHit) return uiDist <= avatarDist ? "UI" : "Avatar";
        if (uiHit) return "UI";
        if (avatarHit) return "Avatar";
        return "None";
    }

    bool TryGetUiHitDistance(Ray ray, out float distance)
    {
        distance = 0f;
        if (!uiRect) return false;

        Plane p = new Plane(uiRect.forward, uiRect.position);
        if (!p.Raycast(ray, out float enter)) return false;
        if (enter <= 0f) return false;

        Vector3 hitWorld = ray.GetPoint(enter);
        Vector3 local = uiRect.InverseTransformPoint(hitWorld);
        if (!IsInsideRectWithPadding(uiRect, new Vector2(local.x, local.y))) return false;

        distance = enter;
        return true;
    }

    bool IsInsideRectWithPadding(RectTransform targetRect, Vector2 local)
    {
        if (!targetRect) return false;
        Rect r = targetRect.rect;
        float pad = Mathf.Clamp01(uiInnerPaddingPercent);
        float padX = r.width * pad;
        float padY = r.height * pad;

        float minX = r.xMin + padX;
        float maxX = r.xMax - padX;
        float minY = r.yMin + padY;
        float maxY = r.yMax - padY;

        if (minX >= maxX || minY >= maxY) return false;
        return local.x >= minX && local.x <= maxX && local.y >= minY && local.y <= maxY;
    }

    bool TryGetAvatarHitDistance(Ray ray, out float distanceAlongRay)
    {
        distanceAlongRay = 0f;
        if (!avatarHead) return false;

        Vector3 toPoint = avatarHead.position - ray.origin;
        float t = Vector3.Dot(toPoint, ray.direction);
        if (t <= 0f) return false;

        Vector3 closest = ray.origin + ray.direction * t;
        float dist = Vector3.Distance(closest, avatarHead.position);
        if (dist > Mathf.Max(0.01f, avatarHitRadius)) return false;

        distanceAlongRay = t;
        return true;
    }

    void FlushSessionLog(string result)
    {
        if (!_sessionActive || _gameStartTime < 0f) return;

        if (gazeCamera != null)
        {
            float interval = Mathf.Max(0.1f, sampleIntervalSeconds);
            while (Time.time >= _nextSampleTime)
            {
                int second = Mathf.Max(0, Mathf.FloorToInt(_nextSampleTime - _gameStartTime));
                _gazeSamples.Add($"{second},{GetCurrentGazeLabel()}");
                _nextSampleTime += interval;
            }
        }

        float endTime = Time.time;
        float totalTime = endTime - _gameStartTime;

        // Formatting the log file
        StringBuilder sb = new StringBuilder();
        sb.AppendLine("Simon Session Log");
        sb.AppendLine($"Timestamp: {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
        sb.AppendLine($"ParticipantId: {participantId}");
        sb.AppendLine($"AvatarNumber: {avatarNumber}");
        sb.AppendLine($"Result: {result}");
        sb.AppendLine($"TotalTimeFromStartPress_sec: {totalTime:F3}");
        sb.AppendLine();
        sb.AppendLine("PerSecondGaze: second,label");
        for (int i = 0; i < _gazeSamples.Count; i++)
            sb.AppendLine(_gazeSamples[i]);

        string logsDir = Path.Combine(Application.persistentDataPath, "simon_logs");
        Directory.CreateDirectory(logsDir);
        string fileName = $"session_{DateTime.Now:yyyyMMdd_HHmmss}.txt";
        string filePath = Path.Combine(logsDir, fileName);
        File.WriteAllText(filePath, sb.ToString(), Encoding.UTF8);

#if UNITY_ANDROID && !UNITY_EDITOR
        // Extra copy for adb_pull
        TryWriteAndroidPublicCopy(fileName, sb.ToString());
#endif

        Debug.Log($"[Logger] Session log saved: {filePath}");
        _sessionActive = false;
    }

#if UNITY_ANDROID && !UNITY_EDITOR
    void TryWriteAndroidPublicCopy(string fileName, string content)
    {
        try
        {
            string publicDir = "/sdcard/Download/simon_logs";
            Directory.CreateDirectory(publicDir);
            string publicPath = Path.Combine(publicDir, fileName);
            File.WriteAllText(publicPath, content, Encoding.UTF8);
            Debug.Log($"[Logger] Android public copy saved: {publicPath}");
        }
        catch (Exception e)
        {
            Debug.LogWarning($"[Logger] Failed to write public Android log copy: {e.Message}");
        }
    }
#endif
}
