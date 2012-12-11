Logotouch v2
============

This project is the second version of
[Logotouch](https://github.com/tito/logotouch). It aim to create a multiuser
environment to create sentence from various words. Each words can be
manipulated with different gesture to change the meaning of the word.

Currently in development.

Redis schema
------------

```
corpus
  .[id]
    .name                    - Name of the corpus
      .email                 - Email of the owner
      .author                - Name of the owner
	  .lastupdate            - Date of the latest update done on the corpus
	  .version               - Version of the corpus (can be used for caching)
      .[id]
        .type                - Type of the word (0, 1, 2)
        .{present,future,past,infinitif}_[1..]
          .zoomout           - (list) Words used for zoomout (usually, 3 levels)
          .zoomin            - (list) Words used for zoomin (usually, 3 levels)
          .normal            - (list) Words used by default
		  .opposite          - (list) Words used for opposite
          .shake             - (list) Words used when shake
```

The "opposite" and "shake" make sense only for the "normal" word.
