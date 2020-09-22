# YCrawler

### Scoring API

Async crawler for news.ycombinator.com.
Process 30 top news. Download news and all page from links in news's comments.

### Requirements

You need Python 3.7+

### Using

To start  execute:

```
python3  main.py 
```  
optional arguments:

```      
	--save_path directory to save pages content, default = '.'
    --period    period between crawler iterations in seconds, default = 5*60 
```

