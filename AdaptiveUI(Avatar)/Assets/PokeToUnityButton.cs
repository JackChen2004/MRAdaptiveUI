using UnityEngine;
using UnityEngine.UI;

public class PokeToUnityButton : MonoBehaviour
{
    public Button button;

    private float _lastTime;
    public float cooldown = 0.2f;

    void Awake()
    {
        if (!button) button = GetComponent<Button>();
    }

    public void Click()
    {
        if (!button) return;
        if (Time.time - _lastTime < cooldown) return;

        _lastTime = Time.time;
        button.onClick.Invoke();
    }
}