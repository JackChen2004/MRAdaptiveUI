using UnityEngine;
using UnityEngine.UI;

// Pass the click event to game manager
public class SimonButtonRelay : MonoBehaviour
{
    public SimonGameManager game;
    public SimonColorId colorId;

    private void Awake()
    {
        GetComponent<Button>().onClick.AddListener(() => game.OnUserInput(colorId));
    }
}