using UnityEngine;
using System;

public class SimonUIAutoReposition : MonoBehaviour
{
    public event Action<bool> OnUiMovedStateChanged;

    public enum MoveDir { Up, Down, Left, Right }

    [Header("References")]
    public Camera mainCam;
    public Transform followTarget;   
    public RectTransform uiRect;    
    public Transform avatarHead;

    [Header("Movement")]
    public bool forceStaticUi = false; 
    public bool followTargetMotion = true;
    public float moveSpeed = 2.0f;   
    public MoveDir moveDir = MoveDir.Up;
    public float avoidDistance = 0.1f;

    [Header("Detection")]
    public float maxAvatarDistanceForAdaptive = 5.0f;
    public float headYOffset = 0.2f;
    public float occlusionResponse = 6f;      

    [Header("Rotation")]
    public float rotateLerpSpeed = 12f;

    Vector3 _startPos;
    Quaternion _startRot;
    Vector3 _followLocalOffset;
    float _avoidBlend; 
    bool _uiMoved;
    bool _snapped;

    void Reset()
    {
        mainCam = Camera.main;
    }

    void Awake()
    {
        _startPos = transform.position;
        _startRot = transform.rotation;

        if (!mainCam) mainCam = Camera.main;
        if (!followTarget && mainCam) followTarget = mainCam.transform;
        if (!uiRect)
        {
            Canvas c = GetComponentInChildren<Canvas>();
            if (c) uiRect = c.GetComponent<RectTransform>();
        }

        if (followTargetMotion && followTarget)
        {
            Quaternion yaw = GetYawRotation(followTarget);
            _followLocalOffset = Quaternion.Inverse(yaw) * (transform.position - followTarget.position);
        }
    }

    void Update()
    {
        Vector3 basePos = GetBasePosition();
        UpdateAvoidBlend(basePos);
        Vector3 targetPos = basePos + GetAvoidDirection() * avoidDistance * _avoidBlend;
        UpdateMovedState();

        // Snap instantly to avoid startup drift animation
        if (!_snapped)
        {
            transform.position = targetPos;

            if (followTarget)
            {
                Vector3 forward = followTarget.forward;
                forward.y = 0f;
                if (forward.sqrMagnitude > 0.0001f)
                    transform.rotation = Quaternion.LookRotation(forward.normalized, Vector3.up);
            }

            _snapped = true;
            return;
        }

        transform.position = Vector3.MoveTowards(
            transform.position,
            targetPos,
            moveSpeed * Time.deltaTime
        );

        if (followTarget)
        {
            Vector3 forward = followTarget.forward;
            forward.y = 0f;
            if (forward.sqrMagnitude > 0.0001f)
            {
                Quaternion targetRot = Quaternion.LookRotation(forward.normalized, Vector3.up);
                transform.rotation = Quaternion.Slerp(
                    transform.rotation,
                    targetRot,
                    rotateLerpSpeed * Time.deltaTime
                );
            }
        }
    }

    void UpdateMovedState()
    {
        bool moved = _avoidBlend > 0.5f;
        if (moved == _uiMoved) return;
        _uiMoved = moved;
        OnUiMovedStateChanged?.Invoke(_uiMoved);
    }

    void UpdateAvoidBlend(Vector3 basePos)
    {
        bool occluding = false;
        bool adaptiveAllowed = !forceStaticUi && mainCam && uiRect && avatarHead;

        if (adaptiveAllowed)
        {
            float avatarDistToUser = Vector3.Distance(mainCam.transform.position, avatarHead.position);
            if (avatarDistToUser > maxAvatarDistanceForAdaptive)
                adaptiveAllowed = false;
        }

        if (adaptiveAllowed)
        {
            Vector3 uiOffsetFromAnchor = uiRect.position - transform.position;
            Vector3 uiBasePos = basePos + uiOffsetFromAnchor;

            // Evaluate occlusion at base position
            occluding = IsUiOccludingHeadAtPose(uiBasePos, uiRect.rotation);
        }

        float target = _avoidBlend;

        if (!adaptiveAllowed)
        {
            target = 0f;
        }
        else if (occluding)
        {
            target = 1f;
        }
        else
        {
            target = 0f;
        }

        float speed = Mathf.Max(0.01f, occlusionResponse);
        _avoidBlend = Mathf.MoveTowards(_avoidBlend, target, speed * Time.deltaTime);
    }

    bool IsUiOccludingHeadAtPose(Vector3 uiWorldPos, Quaternion uiWorldRot)
    {
        Vector3 headWorld = avatarHead.position + Vector3.up * headYOffset;
        Vector3 headScreen = mainCam.WorldToScreenPoint(headWorld);

        if (headScreen.z <= 0f) return false;
        if (headScreen.x < 0f || headScreen.x > Screen.width || headScreen.y < 0f || headScreen.y > Screen.height) return false;

        Vector3 camPos = mainCam.transform.position;
        Vector3 toHead = headWorld - camPos;
        float headDist = toHead.magnitude;
        if (headDist <= 0.0001f) return false;

        Vector3 uiForward = uiWorldRot * Vector3.forward;
        Plane uiPlane = new Plane(uiForward, uiWorldPos);
        Ray ray = new Ray(camPos, toHead / headDist);

        if (!uiPlane.Raycast(ray, out float enter)) return false;
        if (enter < 0f) return false;
        if (enter >= headDist) return false; // UI not in front of head

        Vector3 hitWorld = ray.GetPoint(enter);
        if (!IsInsideInnerRectAtPose(hitWorld, uiWorldPos, uiWorldRot)) return false;

        Vector3[] corners = GetUiWorldCornersAtPose(uiWorldPos, uiWorldRot);
        float uiClosestDist = float.PositiveInfinity;
        for (int i = 0; i < 4; i++)
        {
            float d = Vector3.Distance(camPos, corners[i]);
            if (d < uiClosestDist) uiClosestDist = d;
        }

        return uiClosestDist < headDist;
    }

    bool IsInsideInnerRectAtPose(Vector3 worldPoint, Vector3 uiWorldPos, Quaternion uiWorldRot)
    {
        Matrix4x4 localFromWorld = Matrix4x4.TRS(uiWorldPos, uiWorldRot, uiRect.lossyScale).inverse;
        Vector3 local3 = localFromWorld.MultiplyPoint3x4(worldPoint);
        Vector2 local = new Vector2(local3.x, local3.y);
        Rect r = uiRect.rect;

        float minX = r.xMin;
        float maxX = r.xMax;
        float minY = r.yMin;
        float maxY = r.yMax;

        if (minX >= maxX || minY >= maxY) return false;
        return local.x >= minX && local.x <= maxX && local.y >= minY && local.y <= maxY;
    }

    Vector3[] GetUiWorldCornersAtPose(Vector3 uiWorldPos, Quaternion uiWorldRot)
    {
        Rect r = uiRect.rect;
        Vector3 s = uiRect.lossyScale;

        Vector3 bl = new Vector3(r.xMin * s.x, r.yMin * s.y, 0f);
        Vector3 tl = new Vector3(r.xMin * s.x, r.yMax * s.y, 0f);
        Vector3 tr = new Vector3(r.xMax * s.x, r.yMax * s.y, 0f);
        Vector3 br = new Vector3(r.xMax * s.x, r.yMin * s.y, 0f);

        return new Vector3[]
        {
            uiWorldPos + uiWorldRot * bl,
            uiWorldPos + uiWorldRot * tl,
            uiWorldPos + uiWorldRot * tr,
            uiWorldPos + uiWorldRot * br
        };
    }

    Vector3 GetBasePosition()
    {
        if (followTargetMotion && followTarget)
            return followTarget.position + GetYawRotation(followTarget) * _followLocalOffset;

        return _startPos;
    }

    Vector3 GetAvoidDirection()
    {
        Transform basis = followTarget ? followTarget : transform;

        Vector3 f = basis.forward;
        f.y = 0f;
        if (f.sqrMagnitude < 0.0001f) f = Vector3.forward;

        Vector3 right = Vector3.Cross(Vector3.up, f.normalized).normalized;
        Vector3 up = Vector3.up;

        return moveDir switch
        {
            MoveDir.Up => up,
            MoveDir.Down => -up,
            MoveDir.Left => -right,
            MoveDir.Right => right,
            _ => up
        };
    }

    Quaternion GetYawRotation(Transform t)
    {
        Vector3 forward = t.forward;
        forward.y = 0f;
        if (forward.sqrMagnitude < 0.0001f) forward = Vector3.forward;
        return Quaternion.LookRotation(forward.normalized, Vector3.up);
    }

    public float MoveSpeed => moveSpeed;
    public MoveDir MoveDirection => moveDir;
    public float MoveDistance => avoidDistance;
    public bool IsUiMoved => _uiMoved;
}