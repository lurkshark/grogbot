export type NormalizedFeedItem = {
  title: string;
  date: string;
  link: string;
  guid: string;
  author?: string;
  categories?: string[];
  source?: string;
  content: string;
};
