import { TodayData } from "../api/client";
import Character from "../character/Character";
import { CharacterId, Expression } from "../character/types";
import SpeechBubble from "./SpeechBubble";
import "./speech-bubble.css";

type Props = {
  data: TodayData;
  characterId: CharacterId;
  bubbleLoading?: boolean;
  onHedgehogTap?: () => void;
};

export default function TodayView({
  data,
  characterId,
  bubbleLoading,
  onHedgehogTap,
}: Props) {
  return (
    <>
      <Character
        characterId={characterId}
        mood={data.mood}
        expression={data.expression as Expression}
        isSpeaking={bubbleLoading}
        name={data.hedgehog_name}
        onTap={onHedgehogTap}
      />
      <SpeechBubble
        key={data.bubble_text}
        text={data.bubble_text}
        speaker={data.hedgehog_name}
        loading={bubbleLoading}
      />
      {data.is_special_date && data.special_date_label && (
        <p className="special-badge">{data.special_date_label}</p>
      )}
      {data.weather && (
        <div className="weather-card">
          <h3>Időjárás — {data.weather.city}</h3>
          <p>
            {data.weather.temp_c != null ? `${data.weather.temp_c}°C` : "—"},{" "}
            {data.weather.description_hu}
          </p>
        </div>
      )}

      {data.poem && (
        <div className="content-card">
          <h3>{data.poem.title ?? "Mai vers"}</h3>
          <p className="content-card-body">{data.poem.text}</p>
        </div>
      )}

      {data.book_tip && (
        <div className="content-card">
          <h3>{data.book_tip.title ?? "Könyvajánló"}</h3>
          <p className="content-card-body">{data.book_tip.text}</p>
        </div>
      )}

      {data.movie_tip && (
        <div className="content-card">
          <h3>{data.movie_tip.title ?? "Film ajánló"}</h3>
          <p className="content-card-body">{data.movie_tip.text}</p>
        </div>
      )}

      {data.news && (
        <div className="content-card">
          <h3>{data.news.title ?? "Mai hírek"}</h3>
          <p className="content-card-body">{data.news.text}</p>
          {data.news.items && data.news.items.length > 0 && (
            <ul className="content-links">
              {data.news.items.map((it, i) => (
                <li key={i}>
                  {it.url ? (
                    <a href={it.url} target="_blank" rel="noreferrer">
                      {it.title}
                    </a>
                  ) : (
                    it.title
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {data.health && (
        <div className="content-card">
          <h3>{data.health.title ?? "Egészség"}</h3>
          <p className="content-card-body">{data.health.text}</p>
          {data.health.items && data.health.items.length > 0 && (
            <ul className="content-links">
              {data.health.items.map((it, i) => (
                <li key={i}>
                  {it.url ? (
                    <a href={it.url} target="_blank" rel="noreferrer">
                      {it.title}
                    </a>
                  ) : (
                    it.title
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </>
  );
}
