# #!/usr/bin/env python3
#
# from pydantic import BaseModel
#
#
# class Download(BaseModel):
#     def fetch_arbetsformedlingen_historical_job_ads():
#         raise NotImplementedError("rewrite to just get the pickle")
#         # logger = logging.getLogger(__name__)
#         # # for now we only support the 400 MB data in zip from 2021
#         # # download chosen language file
#         # url = "https://minio.arbetsformedlingen.se/historiska-annonser/2021_first_6_months.zip"
#         # # inspired by http://stackoverflow.com/questions/15644964/ddg#15645088
#         # # this will take only -1 split part of the url
#         # filename = "data_arbetsformedlingen_historical_job_ads_" + url.split("/")[-1]
#         # json_filename = filename.replace("zip", "json")
#         # jsonl_filename = f"{json_filename}l"
#         # pickle_filename = SupportedPicklePaths.ARBETSFORMEDLINGEN_HISTORICAL_ADS.value
#         # if os.path.isfile(pickle_filename):
#         #     logging.info(
#         #         _(
#         #             "Historical Ads data from the Swedish Public Employment Service has "
#         #             "already been downloaded and converted."
#         #         )
#         #     )
#         # else:
#         #     tui.arbetsformedlingen_historical_job_ads_download()
#         #     if not exists(filename):
#         #         with open(filename, "wb") as output_file:
#         #             response = requests.get(url, stream=True)
#         #             total_length = response.headers.get("content-length")
#         #             if total_length is None:
#         #                 # no content length header
#         #                 output_file.write(response.content)
#         #             else:
#         #                 dl = 0
#         #                 total_length = int(total_length)
#         #                 for data in response.iter_content(chunk_size=4096):
#         #                     dl += len(data)
#         #                     output_file.write(data)
#         #                     done = int(50 * dl / total_length)
#         #                     sys.stdout.write(
#         #                         "\r[{}{}]".format("=" * done, " " * (50 - done))
#         #                     )
#         #                     sys.stdout.flush()
#         #
#         #         print("\nDownload Completed!!!")
#         #     else:
#         #         if exists(filename) and not exists(json_filename):
#         #             print("Decompressing file")
#         #             with ZipFile(filename, "r") as zip:
#         #                 # list all the contents of the zip file
#         #                 zip.printdir()
#         #                 # extract all files
#         #                 print("extraction...")
#         #                 zip.extractall()
#         #                 move("2021_first_6_months.json", json_filename)
#         #         elif exists(filename) and exists(json_filename):
#         #             if not exists(jsonl_filename):
#         #                 print("Converting to JSON Lines")
#         #                 with open(jsonl_filename, "w") as outfile:
#         #                     count = 1
#         #                     for entry in json.load(open(json_filename)):
#         #                         json.dump(entry, outfile)
#         #                         outfile.write("\n")
#         #                         if count % 100 == 0:
#         #                             print(count)
#         #                         count += 1
#         #             if not exists(pickle_filename):
#         #                 print(
#         #                     "Parsing the first 100.000 lines of the data into a Pandas DataFrame. "
#         #                     "This might take a while."
#         #                 )
#         #                 start = time.time()
#         #                 with open(jsonl_filename) as file:
#         #                     df = pd.DataFrame()
#         #                     count = 1
#         #                     for line in file:
#         #                         ad = HistoricalJobAd(line)
#         #                         df = df.append(
#         #                             pd.DataFrame(
#         #                                 data=[dict(id=ad.id, text=ad.text, object=ad)]
#         #                             )
#         #                         )
#         #                         if count % 1000 == 0:
#         #                             print(count)
#         #                         if count == 100000:
#         #                             break
#         #                         count += 1
#         #                     df.to_pickle(pickle_filename)
#         #                 end = time.time()
#         #                 logger.info(f"Duration: {end - start}")
#         #             print("Done!")
#         #         else:
#         #             logging.error("Error. Download failed. Report this bug.")
#
#
#     # def fetch_europarl():
#     #     logger = logging.getLogger(__name__)
#     #     # for now we only support europarl data from
#     #     # https://github.com/egils-consulting/LexUse-data
#     #     # download chosen language file
#     #     url = (
#     #         "https://github.com/egils-consulting/LexUse-data/raw/master/"
#     #         + f"{config.language_code}.xz"
#     #     )
#     #     # inspired by http://stackoverflow.com/questions/15644964/ddg#15645088
#     #     # this will take only -1 split part of the url
#     #     filename = "data_" + url.split("/")[-1]
#     #     txt_filename = filename.replace("xz", "txt")
#     #     if os.path.isfile(txt_filename):
#     #         logging.info(_(f"Data for {config.language} has " + "already been downloaded."))
#     #     else:
#     #         tui.europarl_download()
#     #         with open(filename, "wb") as output_file:
#     #             response = requests.get(url, stream=True)
#     #             total_length = response.headers.get("content-length")
#     #             if total_length is None:
#     #                 # no content length header
#     #                 output_file.write(response.content)
#     #             else:
#     #                 dl = 0
#     #                 total_length = int(total_length)
#     #                 for data in response.iter_content(chunk_size=4096):
#     #                     dl += len(data)
#     #                     output_file.write(data)
#     #                     done = int(50 * dl / total_length)
#     #                     sys.stdout.write("\r[{}{}]".format("=" * done, " " * (50 - done)))
#     #                     sys.stdout.flush()
#     #
#     #         print("\nDownload Completed!!!")
#     #
#     #         if os.path.isfile(filename):
#     #             print("Decompressing file")
#     #             with lzma.open(filename, "rb") as f:
#     #                 # f is now the uncompressed object
#     #                 # write it to
#     #                 with open(txt_filename, "wb") as out:
#     #                     out.write(f.read())
#     #         else:
#     #             logging.error("Error. Download failed. Report this bug.")
