using UnityEngine;
using UnityEngine.UI;
using PassthroughCameraSamples.MultiObjectDetection;

public class UIDetectMovement : MonoBehaviour
{
    public SentisInferenceUiManager detectionUiManager;
    public string targetClass = "person";
    public RawImage displayImage;

    [Header("Gazing")]
    public Transform head;          
    public float distance = 1.2f;

    [Header("Height")]
    public float baseHeight = -0.05f;
    public float liftedHeight = 0.25f;

    [Header("Smoothness")]
    public float followSmooth = 15f;
    public float heightSmooth = 8f;

    [Header("Occlusion Check (Tolerance)")]
    public float occlusionPaddingPx = 20f;

    private float currentHeight;
    private Camera headCam;

    void Reset()
    {
        if (head == null && Camera.main != null) head = Camera.main.transform;
    }

    void Start()
    {
        currentHeight = baseHeight;

        if (head != null)
            headCam = head.GetComponent<Camera>() ?? head.GetComponentInChildren<Camera>();

        if (headCam == null) headCam = Camera.main;
    }

    void Update()
    {
        if (head == null) return;

        float targetHeight = baseHeight;
        Vector3 predictedPos =
            head.position +
            head.forward * distance +
            head.up * currentHeight;

        bool occludingPerson = IsOccludingPersonOnDisplay(predictedPos);
        targetHeight = occludingPerson ? liftedHeight : baseHeight;
        currentHeight = Mathf.Lerp(currentHeight, targetHeight, heightSmooth * Time.deltaTime);

        Vector3 targetPos =
            head.position +
            head.forward * distance +
            head.up * currentHeight;

        transform.position = Vector3.Lerp(transform.position, targetPos, followSmooth * Time.deltaTime);
    }

    // Person occulusion check
    bool IsOccludingPersonOnDisplay(Vector3 sphereWorldPos)
    {
        Vector3 vp = headCam.WorldToViewportPoint(sphereWorldPos);
        if (vp.z <= 0f || vp.x < 0f || vp.x > 1f || vp.y < 0f || vp.y > 1f)
            return false;

        RectTransform rt = displayImage.rectTransform;
        float displayW = rt.rect.width;
        float displayH = rt.rect.height;

        Vector2 sphereLocal = new Vector2(
            displayW * (vp.x - 0.5f),
            displayH * (vp.y - 0.5f)
        );

        var boxes = detectionUiManager.BoxDrawn;

        for (int i = 0; i < boxes.Count; i++)
        {
            var b = boxes[i];
            if (b.ClassName != targetClass) continue;

            float boxX = b.CenterX;
            float boxY = -b.CenterY;

            float halfW = b.Width * 0.5f + occlusionPaddingPx;
            float halfH = b.Height * 0.5f + occlusionPaddingPx;

            bool inside =
                sphereLocal.x >= boxX - halfW && sphereLocal.x <= boxX + halfW &&
                sphereLocal.y >= boxY - halfH && sphereLocal.y <= boxY + halfH;

            if (inside) return true;
        }

        return false;
    }
}