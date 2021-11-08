import pandas as pd
import numpy as np
import math

MINIMUM_CONFIDENCE = 0.8
FRAME_RATE = 30
PIXEL_RATIO = 0.007124


def get_angle(a, b, c):
    ang = math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0]))
    return ang + 360 if ang < 0 else ang


def format_excel_csv(excel_path):
    df = pd.read_csv(excel_path)
    new_header = df.iloc[0] + "_" + df.iloc[1]
    df.columns = new_header
    df = df.iloc[2:]
    df = df.apply(pd.to_numeric, errors='coerce')
    return df


class Data:
    def __init__(self, excel_path):
        # Data
        self.df = format_excel_csv(excel_path)
        self.frame_size = len(self.df)
        self.athlete_vel = [0, 0, 0, 0, 0] + self.get_velocity_of_point("waist")[0] + [0, 0]
        self.athlete_vel_avg = [0, 0, 0, 0, 0] + self.get_velocity_of_point("waist")[3] + [0, 0]
        self.leg_angles = self.get_side_view_angles("leg")[0]

        # Special Frames
        self.start_pull = [5] + self.get_start_pull_frames()
        self.end_pull = self.get_end_pull_frames()
        self.finish_drive = self.get_finish_drive_frames()
        self.kick_recovery = self.get_kick_recovery_frames()
        self.kick_propulsion = self.get_kick_propulsion_frames()
        self.finish_kick = self.get_finish_kick_frames()

    def get_average_velocity(self):
        return round(np.average(self.athlete_vel_avg), 3)

    def get_stroke_rate(self):
        return round(len(self.finish_kick) / ((self.frame_size / FRAME_RATE) / 60), 3)

    def get_stroke_length(self):
        altered_df = self.df.filter(["waist_x", "waist_likelihood"])
        lengths = []
        previous_index = -1
        for index in self.finish_kick:
            if previous_index == -1:
                previous_index = index
                continue
            pixel_difference = altered_df["waist_x"][previous_index] - altered_df["waist_x"][index]
            lengths.append(pixel_difference * PIXEL_RATIO)
            previous_index = index
        return round(np.average(lengths), 3)

    def get_velocity_of_point(self, point):
        altered_df = self.df.filter([f"{point}_x", f"{point}_y", f"{point}_likelihood"], axis=1)
        altered_df.index = np.arange(0, len(altered_df))
        pixel_meters = PIXEL_RATIO * 30  # Meters/pixel * (1 second = 30 frames)
        velocities = []
        differences = []
        likelihoods = []
        avg_vel = []
        print("Calculating Velocities")
        for index, row in altered_df.iterrows():
            if index > 7:
                difference = abs(altered_df[f'{point}_x'][index - 1] - altered_df[f'{point}_x'][index])
                differences.append(difference)
                if altered_df[f'{point}_likelihood'][index] >= MINIMUM_CONFIDENCE and difference < 2.5 * np.average(
                        differences[-5:]):
                    velocities.append(round(difference * pixel_meters, 3))
                    avg_vel.append(np.average(velocities[-4:]))
                else:
                    altered_df[f'{point}_x'][index] = altered_df[f'{point}_x'][index] + np.average(differences[
                                                                                                        -3:])
                    velocities.append(abs(altered_df[f'{point}_x'][index - 1] - altered_df[f'{point}_x'][index])
                                      * pixel_meters)
        print("===============")
        print("Returning Velocities")
        return avg_vel, altered_df, likelihoods, avg_vel

    def get_side_view_angles(self, point):
        angles = []
        likelihood = []
        print("Calculating Angles")
        for index, row in self.df.iterrows():
            if point == "leg":
                likelihood.append((row["waist_likelihood"] + row["knee_likelihood"] + row["foot_likelihood"]) / 3)
                waist = np.array([row["waist_x"], row["waist_y"]])
                knee = np.array([row["knee_x"], row["knee_y"]])
                foot = np.array([row["foot_x"], row["foot_y"]])
                angle = round(get_angle(waist, knee, foot))
                if index > 4:
                    print(np.std(angles[-3:]))
                if (row["waist_likelihood"] and row["knee_likelihood"] and row["foot_likelihood"]) > 0.9:
                    angles.append(angle)
                else:
                    angles.append(np.nan)
            elif point == "arm":
                likelihood.append((row["wrist_likelihood"] + row["elbow_likelihood"] + row["shoulder_likelihood"]) / 3)
                waist = np.array([row["wrist_x"], row["wrist_y"]])
                knee = np.array([row["elbow_x"], row["elbow_y"]])
                foot = np.array([row["shoulder_x"], row["shoulder_y"]])
                angle = round(get_angle(waist, knee, foot))
                if (row["wrist_likelihood"] and row["elbow_likelihood"] and row["shoulder_likelihood"]) > MINIMUM_CONFIDENCE:
                    angles.append(angle)
                else:
                    angles.append(np.nan)

        print("Returning Angles")
        return angles, likelihood

    def get_start_pull_frames(self):
        altered_df = self.df.filter(["wrist_x", "wrist_likelihood", "shoulder_x", "shoulder_likelihood"])
        distance_deltas = []
        frames = [0]
        for index, row in altered_df.iterrows():
            if altered_df["wrist_likelihood"][index] > MINIMUM_CONFIDENCE and \
                    altered_df["shoulder_likelihood"][index] > MINIMUM_CONFIDENCE:
                if index > 2:
                    temp_distance = abs(altered_df["wrist_x"][index] - altered_df["shoulder_x"][index])
                    if index > 5:
                        if temp_distance < (np.mean(distance_deltas) - 0.6 * np.std(distance_deltas)) \
                                and frames[-1] < index - 5:
                            frames.append(index - 2)
                    distance_deltas.append(temp_distance)
        return frames[1:]

    def get_end_pull_frames(self):
        altered_df = self.df.filter(["wrist_x", "wrist_likelihood", "waist_x", "waist_likelihood"])
        distance_deltas = []
        frames = [-30]
        previous_distance = math.inf
        for index, row in altered_df.iterrows():
            if altered_df["wrist_likelihood"][index] > MINIMUM_CONFIDENCE and \
                    altered_df["waist_likelihood"][index] > MINIMUM_CONFIDENCE:
                temp_distance = abs(altered_df["wrist_x"][index] - altered_df["waist_x"][index])
                if previous_distance < temp_distance < np.mean(distance_deltas) and frames[-1] < index - 30:
                    frames.append(index - 2)
                previous_distance = temp_distance
                distance_deltas.append(temp_distance)
        return frames[1:]

    def get_finish_drive_frames(self):
        altered_df = self.df.filter(["wrist_x", "wrist_likelihood", "waist_x", "waist_likelihood"])
        distance_deltas = []
        frames = [-30]
        previous_distance = -1
        for index, row in altered_df.iterrows():
            if altered_df["wrist_likelihood"][index] > MINIMUM_CONFIDENCE and \
                    altered_df["waist_likelihood"][index] > MINIMUM_CONFIDENCE:
                temp_distance = abs(altered_df["wrist_x"][index] - altered_df["waist_x"][index])
                if index > 7:
                    if previous_distance > temp_distance and frames[-1] < index - 30:
                        frames.append(index - 2)
                    previous_distance = temp_distance
                distance_deltas.append(temp_distance)
        return frames[1:]

    def get_kick_recovery_frames(self):
        previous_angle = math.inf
        frames = [-30]
        for frame, angle in enumerate(self.leg_angles):
            if frame > 9:
                if frame == 10:
                    previous_angle = angle
                    continue

                if previous_angle > angle and frames[-1] < frame - 10 and previous_angle - angle > 10:
                    frames.append(frame - 3)
                previous_angle = angle
        return frames[1:]

    def get_kick_propulsion_frames(self):
        previous_angle = math.inf
        frames = [-30]
        for frame, angle in enumerate(self.leg_angles):
            if frame == 0:
                previous_angle = angle
                continue
            if previous_angle < angle and frames[-1] < frame - 30:
                frames.append(frame - 2)
            previous_angle = angle
        return frames[1:]

    def get_finish_kick_frames(self):
        previous_angle = math.inf
        frames = [-30]
        for frame, angle in enumerate(self.leg_angles):
            if frame > 9:
                if frame == 10:
                    previous_angle = angle
                    continue

                if previous_angle > angle and frames[-1] < frame - 35:
                    frames.append(frame - 2)
                previous_angle = angle
        return frames[1:]
