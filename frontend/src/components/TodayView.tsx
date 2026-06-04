import { TodayData } from "../api/client";
import HedgehogStage from "../hedgehog/HedgehogStage";
import SpeechBubble from "./SpeechBubble";
import "./speech-bubble.css";

type Props = {
  data: TodayData;
  onHedgehogTap?: () => void;
};

export default function TodayView({ data, onHedgehogTap }: Props) {
  return (
    <>
      <HedgehogStage
        mood={data.mood}
        name={data.hedgehog_name}
        onTap={onHedgehogTap}
      />
      <SpeechBubble text={data.bubble_text} speaker={data.hedgehog_name} />
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
    </>
  );
}
