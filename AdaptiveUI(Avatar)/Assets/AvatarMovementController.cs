using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;

public class AvatarMovementController : MonoBehaviour
{
    [Header("References")]
    public Animator animator;
    public Transform userHead;

    public AudioSource talkAudioSource;
    public AudioClip talkClip;

    [Header("Movement")]
    public float walkSpeed = 1.2f;
    public float stopDistance = 3.0f;
    public float walkAwaySpeed = 1.2f;
    public float passByDistance = 2.5f;
    public float passBySideOffset = 0.6f;
    public float turnSpeed = 6f;

    [Header("Sequence")]
    public float startDelay = 5.0f;
    public float waveMinSeconds = 1.5f;
    public int waveLoops = 1;
    public float talkMinSeconds = 2.0f;
    public int talkLoops = 1;
    public float nodMinSeconds = 1.0f;
    public int nodLoops = 1;
    public float nodTotalSeconds = 10.0f;
    public float nodIntervalSeconds = 2.0f;
    public bool waitForTalkClipToFinish = true;

    public InputActionProperty resetAction;

    [Header("Animator Triggers")]
    public string idleTrigger = "ToIdle";
    public string walkTrigger = "ToWalk";
    public string waveTrigger = "ToWave";
    public string talkTrigger = "ToTalk";
    public string nodTrigger = "ToNod";

    [Header("Wave State Match")]
    public string waveStateTag = "Wave";
    public string waveStateName = "Wave";

    [Header("Talk State Match")]
    public string talkStateTag = "Talk";
    public string talkStateName = "Talk on the phone";

    [Header("Nod State Match")]
    public string nodStateTag = "Nod";
    public string nodStateName = "Nod";
    public float enterStateTimeout = 1.0f;

    private Vector3 _initPos;
    private Quaternion _initRot;
    private Coroutine _sequenceCo;
    private bool _startedOnce;

    int _idleHash;
    int _walkHash;
    int _waveHash;
    int _talkHash;
    int _nodHash;

    private void Awake()
    {
        if (!animator) animator = GetComponentInChildren<Animator>();
        if (!talkAudioSource) talkAudioSource = GetComponentInChildren<AudioSource>();
        _initPos = transform.position;
        _initRot = transform.rotation;
        CacheTriggerHashes();
    }

    private void OnEnable()
    {
        if (resetAction.action != null)
        {
            resetAction.action.Enable();
            resetAction.action.performed += OnResetPerformed;
        }
    }

    private void OnDisable()
    {
        if (resetAction.action != null)
        {
            resetAction.action.performed -= OnResetPerformed;
            resetAction.action.Disable();
        }
    }

    private void Start()
    {
        ForceIdle();
    }

    private void Update()
    {
        if (OVRInput.GetDown(OVRInput.Button.Two, OVRInput.Controller.RTouch))
        {
            ResetAvatar();
        }
    }

    private void OnResetPerformed(InputAction.CallbackContext ctx)
    {
        ResetAvatar();
    }

    public void StartSequenceFromUIButton()
    {
        if (_startedOnce) return;
        _startedOnce = true;

        if (_sequenceCo != null) StopCoroutine(_sequenceCo);
        _sequenceCo = StartCoroutine(SequenceRoutine());
    }

    private IEnumerator SequenceRoutine()
    {
        // Avatar movement pipeline
        ForceIdle();
        yield return new WaitForSeconds(startDelay);
        SetWalk();
        yield return WalkTowardsUserUntilStopDistance();
        SetWave();
        yield return PlayPhase(
            waveStateTag,
            waveStateName,
            waveMinSeconds,
            waveLoops
        );
        SetTalk();
        StartTalkAudioIfAny();
        yield return PlayPhase(
            talkStateTag,
            talkStateName,
            talkMinSeconds,
            talkLoops
        );

        if (waitForTalkClipToFinish && talkAudioSource != null && talkClip != null)
        {
            while (talkAudioSource.isPlaying)
                yield return null;
        }
        StopTalkAudioIfAny();

        yield return NodRepeatedPhase();

        SetWalk();
        yield return WalkAwayPassBy();

        ForceIdle();

        _sequenceCo = null;
    }

    private void CacheTriggerHashes()
    {
        _idleHash = Animator.StringToHash(idleTrigger);
        _walkHash = Animator.StringToHash(walkTrigger);
        _waveHash = Animator.StringToHash(waveTrigger);
        _talkHash = Animator.StringToHash(talkTrigger);
        _nodHash = Animator.StringToHash(nodTrigger);
    }

    private void SetWalk()
    {
        animator.ResetTrigger(_idleHash);
        animator.ResetTrigger(_talkHash);
        animator.ResetTrigger(_waveHash);
        animator.ResetTrigger(_nodHash);
        animator.SetTrigger(_walkHash);
    }

    private void SetWave()
    {
        animator.ResetTrigger(_idleHash);
        animator.ResetTrigger(_walkHash);
        animator.ResetTrigger(_talkHash);
        animator.ResetTrigger(_nodHash);
        animator.SetTrigger(_waveHash);
    }

    private void SetTalk()
    {
        animator.ResetTrigger(_idleHash);
        animator.ResetTrigger(_walkHash);
        animator.ResetTrigger(_waveHash);
        animator.ResetTrigger(_nodHash);
        animator.SetTrigger(_talkHash);
    }

    private void SetNod()
    {
        animator.ResetTrigger(_idleHash);
        animator.ResetTrigger(_walkHash);
        animator.ResetTrigger(_waveHash);
        animator.ResetTrigger(_talkHash);
        animator.SetTrigger(_nodHash);
    }

    private void ForceIdle()
    {
        animator.ResetTrigger(_walkHash);
        animator.ResetTrigger(_talkHash);
        animator.ResetTrigger(_waveHash);
        animator.ResetTrigger(_nodHash);
        animator.SetTrigger(_idleHash);
    }

    private IEnumerator WalkTowardsUserUntilStopDistance()
    {
        while (userHead != null)
        {
            Vector3 target = userHead.position;
            target.y = transform.position.y;

            float dist = Vector3.Distance(transform.position, target);
            if (dist <= stopDistance) break;

            FaceTowards(target);
            transform.position = Vector3.MoveTowards(transform.position, target, walkSpeed * Time.deltaTime);
            yield return null;
        }
    }

    // Waits for the Animator to enter the given state, then keeps the sequence in state until finished.
    private IEnumerator PlayPhase(string stateTag, string stateName, float minSeconds, int minLoops)
    {
        float elapsed = 0f;
        int loopCount = 0;
        float deadline = Time.time + Mathf.Max(0.1f, enterStateTimeout);
        bool enteredState = false;

        while (Time.time < deadline)
        {
            var info = animator.GetCurrentAnimatorStateInfo(0);
            if (IsTargetState(info, stateTag, stateName))
            {
                enteredState = true;
                break;
            }
            yield return null;
        }

        if (!enteredState)
        {
            while (elapsed < minSeconds)
            {
                elapsed += Time.deltaTime;
                yield return null;
            }
            yield break;
        }

        while (true)
        {
            elapsed += Time.deltaTime;
            var info = animator.GetCurrentAnimatorStateInfo(0);
            loopCount = Mathf.Max(loopCount, Mathf.FloorToInt(info.normalizedTime));

            bool enoughTime = elapsed >= minSeconds;
            bool enoughLoops = loopCount >= Mathf.Max(1, minLoops);
            if (enoughTime && enoughLoops) break;
            yield return null;
        }
    }

    private IEnumerator NodRepeatedPhase()
    {
        float total = Mathf.Max(0f, nodTotalSeconds);
        float interval = Mathf.Max(0.1f, nodIntervalSeconds);

        if (total <= 0f)
        {
            SetNod();
            yield return PlayPhase(nodStateTag, nodStateName, nodMinSeconds, nodLoops);
            yield break;
        }

        float endTime = Time.time + total;
        while (Time.time < endTime)
        {
            SetNod();
            yield return PlayPhase(nodStateTag, nodStateName, nodMinSeconds, nodLoops);

            float remaining = endTime - Time.time;
            if (remaining <= 0f) break;

            float wait = Mathf.Min(interval, remaining);
            yield return new WaitForSeconds(wait);
        }
    }

    private IEnumerator WalkAwayPassBy()
    {
        if (userHead == null) yield break;

        Vector3 userPos = userHead.position;
        userPos.y = transform.position.y;

        Vector3 toUser = userPos - transform.position;
        toUser.y = 0f;
        if (toUser.sqrMagnitude < 0.0001f) toUser = transform.forward;
        Vector3 passDir = toUser.normalized;
        Vector3 side = Vector3.Cross(Vector3.up, passDir).normalized;

        Vector3 target = userPos + passDir * passByDistance + side * passBySideOffset;
        target.y = transform.position.y;

        while (Vector3.Distance(transform.position, target) > 0.05f)
        {
            FaceTowards(target);
            transform.position = Vector3.MoveTowards(transform.position, target, walkAwaySpeed * Time.deltaTime);
            yield return null;
        }
    }

    // Make the avatar always face towards the user
    private void FaceTowards(Vector3 target)
    {
        Vector3 dir = target - transform.position;
        dir.y = 0f;
        if (dir.sqrMagnitude <= 0.0001f) return;
        Quaternion look = Quaternion.LookRotation(dir.normalized, Vector3.up);
        transform.rotation = Quaternion.Slerp(transform.rotation, look, Time.deltaTime * turnSpeed);
    }

    private bool IsTargetState(AnimatorStateInfo info, string stateTag, string stateName)
    {
        if (!string.IsNullOrEmpty(stateTag) && info.IsTag(stateTag)) return true;
        if (!string.IsNullOrEmpty(stateName) && info.IsName(stateName)) return true;
        return false;
    }

    private void StartTalkAudioIfAny()
    {
        if (!talkAudioSource || !talkClip) return;
        talkAudioSource.clip = talkClip;
        talkAudioSource.loop = false;
        talkAudioSource.Play();
    }

    private void StopTalkAudioIfAny()
    {
        if (!talkAudioSource) return;
        if (talkAudioSource.isPlaying) talkAudioSource.Stop();
        talkAudioSource.loop = false;
    }

    public void ResetAvatar()
    {
        if (_sequenceCo != null)
        {
            StopCoroutine(_sequenceCo);
            _sequenceCo = null;
        }

        transform.position = _initPos;
        transform.rotation = _initRot;

        ForceIdle();
    }
}
