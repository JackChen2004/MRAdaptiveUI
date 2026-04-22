using System.Collections;
using System.Collections.Generic;
using System;
using UnityEngine;
using UnityEngine.UI;

public class SimonGameManager : MonoBehaviour
{
    public event Action OnGameStarted;
    public event Action<SimonColorId> OnUserPressed;
    public event Action<int> OnRoundCompleted;
    public event Action<int> OnGameCompleted;
    public event Action<int> OnGameFailed;

    [Header("Game Settings")]
    public int maxRounds = 7;
    public UIColourController ui;
    public Button startButton;
    public Button[] colorButtons; 

    [Header("Timing")]
    public float flashOn = 0.45f;
    public float flashOff = 0.20f;
    public float roundGap = 0.35f;

    private readonly List<SimonColorId> _sequence = new();
    private int _inputIndex = 0;

    // Idle = waiting for Start, Showing = replaying sequence to user, WaitingInput = user's turn to tap.
    private enum State { Idle, Showing, WaitingInput }
    private State _state = State.Idle;

    private void Awake()
    {
        if (startButton != null)
            startButton.onClick.AddListener(StartGame);

        ui.SetGray();
        SetState(State.Idle); 
    }

    public void StartGame()
    {
        StopAllCoroutines();
        _sequence.Clear();
        _inputIndex = 0;

        ui.SetGray();
        SetState(State.Showing); 
        OnGameStarted?.Invoke();
        NextRound();
    }

    private void NextRound()
    {
        if (_sequence.Count >= maxRounds)
        {
            EndGameComplete();
            return;
        }

        _sequence.Add((SimonColorId)UnityEngine.Random.Range(0, 4));
        _inputIndex = 0;
        StartCoroutine(ShowSequence());
    }

    private IEnumerator ShowSequence()
    {
        SetState(State.Showing);

        yield return new WaitForSeconds(0.25f);

        foreach (var c in _sequence)
        {
            ShowColor(c);
            yield return new WaitForSeconds(flashOn);

            ui.SetGray();
            yield return new WaitForSeconds(flashOff);
        }

        ui.SetGray();
        SetState(State.WaitingInput); 
    }
    
    // Called by SimonButtonRelay on each color tap;
    public void OnUserInput(SimonColorId pressed)
    {
        if (_state != State.WaitingInput) return;
        OnUserPressed?.Invoke(pressed);

        var expected = _sequence[_inputIndex];
        if (pressed != expected)
        {
            StopAllCoroutines();
            StartCoroutine(WrongFeedback());
            return;
        }

        _inputIndex++;

        if (_inputIndex >= _sequence.Count)
        {
            OnRoundCompleted?.Invoke(_sequence.Count);

            if (_sequence.Count >= maxRounds)
            {
                EndGameComplete();
                return;
            }

            StartCoroutine(NextRoundAfterDelay());
        }
    }

    private IEnumerator NextRoundAfterDelay()
    {
        SetState(State.Showing);
        yield return new WaitForSeconds(roundGap);

        ui.SetGray();
        NextRound();
    }

    private IEnumerator WrongFeedback()
    {
        SetState(State.Showing);

        ui.SetBlack();
        yield return new WaitForSeconds(0.25f);
        ui.SetGray();
        yield return new WaitForSeconds(0.15f);
        ui.SetBlack();
        yield return new WaitForSeconds(0.25f);
        ui.SetGray();

        OnGameFailed?.Invoke(_sequence.Count);
        SetState(State.Idle); 
    }

    private void EndGameComplete()
    {
        StopAllCoroutines();
        ui.SetGray();
        SetState(State.Idle);
        OnGameCompleted?.Invoke(_sequence.Count);
        Debug.Log($"[Simon] Completed maxRounds = {maxRounds}");
    }

    private void ShowColor(SimonColorId id)
    {
        switch (id)
        {
            case SimonColorId.Red: ui.SetRed(); break;
            case SimonColorId.Yellow: ui.SetYellow(); break;
            case SimonColorId.Green: ui.SetGreen(); break;
            case SimonColorId.Blue: ui.SetBlue(); break;
        }
    }

    private void SetState(State s)
    {
        _state = s;

        bool canPressColors = (s == State.WaitingInput);
        if (colorButtons != null)
        {
            foreach (var b in colorButtons)
                if (b != null) b.interactable = canPressColors;
        }

        if (startButton != null)
            startButton.interactable = (s == State.Idle);
    }
}
