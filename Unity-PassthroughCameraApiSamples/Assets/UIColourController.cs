using UnityEngine;
using UnityEngine.UI;

public class UIColourController : MonoBehaviour
{

    public Image colorPanel;  
    public Color redColor = new Color(1f, 0.2f, 0.2f, 1f);
    public Color yellowColor = new Color(1f, 0.92f, 0.16f, 1f);
    public Color greenColor = new Color(0.2f, 0.85f, 0.3f, 1f);
    public Color defaultGray = new Color(0.7f, 0.7f, 0.7f, 1f);

    void Start()
    {
        if (colorPanel != null)
            colorPanel.color = defaultGray;
    }

    public void SetRed()    => SetPanelColor(redColor);
    public void SetYellow() => SetPanelColor(yellowColor);
    public void SetGreen()  => SetPanelColor(greenColor);

    private void SetPanelColor(Color c)
    {
        if (colorPanel == null) return;
        colorPanel.color = c;
    }
}