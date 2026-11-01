// The realtime half of the widget: a LiveKit room shared with the VoiceServe agent worker.
// Push-to-talk is two RPCs to the agent (start_turn, end_turn); the agent can also end a turn
// itself when it hears the student stop. Captions, agent state and cards arrive over the room.
import {
  type RemoteParticipant,
  type RemoteTrack,
  Room,
  RoomEvent,
  Track,
} from "livekit-client";

export type AgentState = "initializing" | "listening" | "thinking" | "speaking" | "idle";

export interface VoiceEvents {
  agentState(state: AgentState): void;
  transcript(who: "user" | "agent", segmentId: string, text: string, final: boolean): void;
  card(card: unknown): void;
  disconnected(): void;
}

const AGENT_TIMEOUT_MS = 10_000;

export class VoiceClient {
  private readonly room = new Room();
  private agent: RemoteParticipant | null = null;

  constructor(
    private readonly audioHost: ShadowRoot,
    private readonly events: VoiceEvents,
  ) {}

  get connected(): boolean {
    return this.agent !== null && this.room.state === "connected";
  }

  async connect(url: string, token: string): Promise<void> {
    const { room, events } = this;
    room.on(RoomEvent.TrackSubscribed, (track: RemoteTrack) => {
      if (track.kind !== Track.Kind.Audio) return;
      const audio = track.attach();
      audio.hidden = true;
      this.audioHost.append(audio);
    });
    room.on(RoomEvent.TrackUnsubscribed, (track: RemoteTrack) => {
      track.detach().forEach((node) => node.remove());
    });
    room.on(RoomEvent.ParticipantAttributesChanged, (changed, participant) => {
      const state = changed["lk.agent.state"];
      if (state && participant.isAgent) events.agentState(state as AgentState);
    });
    room.on(RoomEvent.DataReceived, (payload, _participant, _kind, topic) => {
      if (topic !== "voiceserve.card") return;
      try {
        events.card(JSON.parse(new TextDecoder().decode(payload)));
      } catch {
        // a malformed card is dropped; the spoken answer still stands
      }
    });
    room.on(RoomEvent.Disconnected, () => {
      this.agent = null;
      events.disconnected();
    });
    room.registerTextStreamHandler("lk.transcription", async (reader, from) => {
      const attributes = reader.info.attributes ?? {};
      const segment = attributes["lk.segment_id"] ?? reader.info.id;
      const final = attributes["lk.transcription_final"] === "true";
      const who = from.identity === room.localParticipant.identity ? "user" : "agent";
      let text = "";
      for await (const chunk of reader) {
        text += chunk;
        events.transcript(who, segment, text, false);
      }
      events.transcript(who, segment, text, final || who === "agent");
    });

    await room.connect(url, token);
    this.agent = await this.waitForAgent();
  }

  private waitForAgent(): Promise<RemoteParticipant> {
    const present = [...this.room.remoteParticipants.values()].find((p) => p.isAgent);
    if (present) return Promise.resolve(present);
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.room.off(RoomEvent.ParticipantConnected, onJoin);
        reject(new Error("The voice agent didn't join"));
      }, AGENT_TIMEOUT_MS);
      const onJoin = (participant: RemoteParticipant) => {
        if (!participant.isAgent) return;
        clearTimeout(timer);
        this.room.off(RoomEvent.ParticipantConnected, onJoin);
        resolve(participant);
      };
      this.room.on(RoomEvent.ParticipantConnected, onJoin);
    });
  }

  private async rpc(method: "start_turn" | "end_turn" | "cancel_turn"): Promise<void> {
    if (!this.agent) throw new Error("Voice isn't connected");
    await this.room.localParticipant.performRpc({
      destinationIdentity: this.agent.identity,
      method,
      payload: "",
    });
  }

  /** Mic on and a new turn; also interrupts the agent if it is speaking (barge-in). */
  async startTurn(): Promise<void> {
    await this.room.startAudio(); // inside the tap's user gesture, so playback is allowed
    await this.room.localParticipant.setMicrophoneEnabled(true);
    await this.rpc("start_turn");
  }

  async endTurn(): Promise<void> {
    await this.rpc("end_turn");
  }

  async cancelTurn(): Promise<void> {
    await this.rpc("cancel_turn").catch(() => undefined);
    await this.micOff();
  }

  async micOff(): Promise<void> {
    await this.room.localParticipant.setMicrophoneEnabled(false);
  }

  async disconnect(): Promise<void> {
    await this.room.disconnect();
  }
}
