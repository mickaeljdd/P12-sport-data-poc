from extract import load_hr, load_sport
from transform import (
    merge_sources,
    fill_missing_sports,
    normalize_transport,
)
from validator import validate
from load import save_csv


class Pipeline:

    def run(self):

        hr = self.extract_hr()

        sport = self.extract_sport()

        df = self.transform(hr, sport)

        df = self.validate(df)

        self.export(df)

    def extract_hr(self):

        return load_hr()

    def extract_sport(self):

        return load_sport()

    def transform(self, hr, sport):

        df = merge_sources(hr, sport)

        df = fill_missing_sports(df)

        df = normalize_transport(df)

        return df

    def validate(self, df):

        return validate(df)

    def export(self, df):

        save_csv(df)